import csv
import io
import os
import shutil
import zipfile
from datetime import datetime
from django.core.files.base import ContentFile
from django.db import transaction
from assets.models import Asset, Product, Vendor, AssetStatus, AssetImage, AssetStatusChoice
from django.db.models import Q
from dashboard.models import Location, Department
from clients.models import Client
from configurations.models import TagConfiguration
from configurations.utils import generate_asset_tag

def parse_csv_file(csv_file):
    rows = []
    errors = []
    try:
        # csv_file is an InMemoryUploadedFile
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file)
        
        if reader.fieldnames:
            expected_headers = {
                'asset_name', 'serial_no', 'tag', 'price', 'purchase_date',
                'warranty_expiry_date', 'description', 'image_filename'
            }
            actual_headers = {h.strip() for h in reader.fieldnames if h}
            
            if 'asset name' in actual_headers:
                actual_headers.add('asset_name')
                
            missing_headers = expected_headers - actual_headers
            if missing_headers:
                missing_str = ', '.join(sorted(missing_headers))
                errors.append(f"Invalid CSV Header: Missing expected column(s): {missing_str}. Please use the provided template.")
                return [], errors
        
        for idx, row in enumerate(reader):
            # Clean row dict keys and values
            clean_row = {k.strip(): v.strip() if v else '' for k, v in row.items() if k}
            
            # Normalize 'asset name' column to 'name' for internal processing
            if 'asset_name' in clean_row and 'name' not in clean_row:
                clean_row['name'] = clean_row.pop('asset_name')
            elif 'asset name' in clean_row and 'name' not in clean_row:
                clean_row['name'] = clean_row.pop('asset name')
            
            # Required field validation
            if not clean_row.get('name'):
                errors.append(f"Row {idx + 1}: 'asset_name' (or 'name') is required.")
                continue
                
            # Date validation and normalization
            for date_col in ['purchase_date', 'warranty_expiry_date']:
                date_val = clean_row.get(date_col)
                if date_val:
                    parsed_date = None
                    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                        try:
                            parsed_date = datetime.strptime(date_val, fmt).date()
                            break
                        except ValueError:
                            pass
                    if not parsed_date:
                        errors.append(f"Row {idx + 1}: invalid {date_col} format.")
                    else:
                        clean_row[date_col] = parsed_date.strftime('%Y-%m-%d')
            
            # Normalize purchase type
            p_type = clean_row.get('purchase_type', '').lower()
            if 'own' in p_type:
                clean_row['purchase_type'] = '1'
            elif 'rent' in p_type:
                clean_row['purchase_type'] = '2'
            else:
                clean_row['purchase_type'] = ''

            rows.append(clean_row)
            
    except Exception as e:
        errors.append(f"Error parsing CSV: {str(e)}")
        
    return rows, errors

def cleanup_bulk_import_files(session_id):
    """
    Delete the temporary directory that holds staged images for a bulk import
    session.  Safe to call even if the directory does not exist.
    """
    staging_dir = os.path.join('media', 'bulk_import', str(session_id))
    if os.path.isdir(staging_dir):
        shutil.rmtree(staging_dir, ignore_errors=True)


def extract_zip_images(zip_file, session_id):
    image_map = {}
    allowed_exts = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    extract_dir = os.path.join('media', 'bulk_import', str(session_id))
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_file, 'r') as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            
            filename = os.path.basename(info.filename)
            ext = os.path.splitext(filename)[1].lower()
            
            if ext in allowed_exts:
                extracted_path = z.extract(info, extract_dir)
                image_map[filename.lower()] = extracted_path
                
    return image_map

def match_images_to_rows(staged_data, image_map):
    matched = 0
    unmatched = 0
    
    for row in staged_data:
        img_file = row.get('image_filename', '').lower().strip()
        if img_file and img_file in image_map:
            row['matched_image_path'] = image_map[img_file]
            row['image_status'] = 'matched'
            matched += 1
        elif img_file:
            row['image_status'] = 'missing'
            unmatched += 1
        else:
            row['image_status'] = 'none'
            
    return staged_data, matched, unmatched

def apply_dept_location_mapping(session, mapping_data, organization):
    staged = session.staged_data
    image_map = session.image_map or {}
    # Build reverse lookup: path -> filename for modal selection matching
    path_to_filename = {v: k for k, v in image_map.items()}
    
    for i, row in enumerate(staged):
        key = str(i)
        if key in mapping_data:
            m = mapping_data[key]
            row['product_target_id']   = m.get('product_id')
            row['vendor_target_id']    = m.get('vendor_id')
            row['client_target_id']    = m.get('client_id')
            row['location_target_id']  = m.get('location_id')
            row['status_target_id']    = m.get('status_id')
            row['purchase_type']       = m.get('purchase_type') or row.get('purchase_type', '')
            
            # Handle image_path from modal selection
            image_path = m.get('image_path')
            if image_path and image_path.strip():
                row['matched_image_path'] = image_path.strip()
                row['image_status'] = 'matched'
            elif 'image_path' in m:
                # Explicitly cleared by user — remove any previous image
                row.pop('matched_image_path', None)
                img_file = row.get('image_filename', '').lower().strip()
                if img_file:
                    row['image_status'] = 'missing'
                else:
                    row['image_status'] = 'none'

    session.staged_data = staged
    session.status = 'mapped'
    session.save()

@transaction.atomic
def commit_bulk_session(session, request):
    created_count = 0
    errors = []

    organization = session.organization
    staged = session.staged_data

    available_status = AssetStatus.objects.filter(name__iexact="Available", organization=organization).first()

    # Pre-fetch all FK data once before the loop
    products_by_id = {str(p.id): p for p in Product.objects.filter(organization=organization)}
    vendors_by_id = {str(v.id): v for v in Vendor.objects.filter(organization=organization)}
    clients_by_id = {str(c.id): c for c in Client.objects.filter(organization=organization)}
    locations_by_id = {str(l.id): l for l in Location.objects.filter(organization=organization)}
    statuses_by_id = {}
    for s in AssetStatus.objects.filter(Q(organization=organization) | Q(organization__isnull=True)):
        statuses_by_id[str(s.id)] = s
    existing_tags = set(Asset.objects.filter(organization=organization).values_list('tag', flat=True))

    tag_config = TagConfiguration.objects.filter(
        organization=organization, use_default_settings=True
    ).first()

    def _get_val(row_dict, key_options):
        for k in key_options:
            for rk, rv in row_dict.items():
                if rk and isinstance(rk, str) and rk.lower() == k.lower():
                    return rv
        return None

    for idx, row in enumerate(staged):
        try:
            prod_id = row.get('product_target_id')
            product = products_by_id.get(prod_id) if prod_id else None
            if not product:
                prod_name = _get_val(row, ['product', 'product name', 'product_name'])
                if prod_name:
                    product = next((p for p in products_by_id.values() if p.name and p.name.lower() == str(prod_name).lower()), None)

            vend_id = row.get('vendor_target_id')
            vendor = vendors_by_id.get(vend_id) if vend_id else None
            if not vendor:
                vend_name = _get_val(row, ['vendor', 'vendor name', 'vendor_name'])
                if vend_name:
                    vendor = next((v for v in vendors_by_id.values() if v.name and v.name.lower() == str(vend_name).lower()), None)

            cli_id = row.get('client_target_id')
            client = clients_by_id.get(cli_id) if cli_id else None
            if not client:
                cli_name = _get_val(row, ['client', 'client name', 'client_name'])
                if cli_name:
                    client = next((c for c in clients_by_id.values() if c.name and c.name.lower() == str(cli_name).lower()), None)

            loc_id = row.get('location_target_id')
            location = locations_by_id.get(loc_id) if loc_id else None
            if not location:
                loc_name = _get_val(row, ['location', 'location name', 'location_name', 'office', 'office name'])
                if loc_name:
                    location = next((l for l in locations_by_id.values() if l.office_name and l.office_name.lower() == str(loc_name).lower()), None)

            status_val = available_status
            status_id = row.get('status_target_id')
            if status_id:
                status_val = statuses_by_id.get(status_id) or available_status
            if not status_id:
                status_name = row.get('status')
                if status_name:
                    custom_status = AssetStatus.objects.filter(
                        Q(organization=organization) | Q(organization__isnull=True),
                        name__iexact=status_name
                    ).first()
                    if custom_status:
                        status_val = custom_status

            tag = row.get('tag')
            if not tag:
                if tag_config:
                    tag = generate_asset_tag(
                        prefix=tag_config.prefix, number_suffix=tag_config.number_suffix
                    )
                else:
                    tag = generate_asset_tag(prefix="VY", number_suffix="001")

            if tag in existing_tags:
                raise ValueError(f"Asset tag '{tag}' already exists. Tags must be unique.")
            existing_tags.add(tag)

            asset = Asset.objects.create(
                organization=organization,
                name=row.get('name'),
                serial_no=row.get('serial_no'),
                tag=tag,
                price=float(row.get('price')) if row.get('price') else None,
                purchase_date=row.get('purchase_date') or None,
                warranty_expiry_date=row.get('warranty_expiry_date') or None,
                purchase_type=row.get('purchase_type'),
                description=row.get('description'),
                product=product,
                vendor=vendor,
                client=client,
                location=location,
                asset_status=status_val
            )

            img_path = row.get('matched_image_path')
            if img_path and os.path.exists(img_path):
                with open(img_path, 'rb') as f:
                    AssetImage.objects.create(
                        asset=asset,
                        image=ContentFile(f.read(), name=os.path.basename(img_path))
                    )

            created_count += 1

        except Exception as e:
            errors.append(f"Row {idx + 1} ({row.get('name')}): {str(e)}")

    if not errors:
        cleanup_bulk_import_files(session.id)
        session.delete()

    return created_count, errors
