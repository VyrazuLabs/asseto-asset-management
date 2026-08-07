import csv
import io
import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from upload.models import BulkUploadSession
from upload.bulk_upload_utils import (
    parse_csv_file, extract_zip_images, match_images_to_rows,
    apply_dept_location_mapping, commit_bulk_session, cleanup_bulk_import_files,
    _get_active_asset_cfs,
)
from dashboard.models import Location, Department
from assets.models import Product, Vendor, AssetStatus
from clients.models import Client
from django.db.models import Q

SESSION_KEY = 'bulk_import_session_id'

# Sample placeholder values for each field type shown in the template CSV
_CF_TYPE_SAMPLE = {
    "text":    "Example text",
    "integer": "10",
    "decimal": "99.99",
    "date":    "2024-01-15",
    "boolean": "Yes",
    "email":   "example@email.com",
}

@login_required
# @permission_required('assets.add_asset') # Assuming permission exists or bypassing for now
def bulk_import_step1(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        zip_file = request.FILES.get('zip_file')
        
        if not csv_file:
            messages.error(request, "CSV file is required.")
            return redirect('upload:bulk_import_step1')
            
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "File must be a CSV.")
            return redirect('upload:bulk_import_step1')
            
        # Pass organization so custom field validation runs
        rows, errors = parse_csv_file(csv_file, organization=request.user.organization)
        if errors:
            for err in errors[:5]:
                messages.error(request, err)
            if len(errors) > 5:
                messages.error(request, f"...and {len(errors)-5} more errors.")
            return redirect('upload:bulk_import_step1')
            
        if not rows:
            messages.error(request, "CSV file is empty or missing data.")
            return redirect('upload:bulk_import_step1')

        # If a previous session exists (user restarted without cancelling),
        # clean up its staged files and DB record before creating a new one.
        existing_session_id = request.session.get(SESSION_KEY)
        if existing_session_id:
            cleanup_bulk_import_files(existing_session_id)
            BulkUploadSession.objects.filter(
                id=existing_session_id,
                organization=request.user.organization
            ).delete()

        # Create session
        session = BulkUploadSession.objects.create(
            organization=request.user.organization,
            created_by=request.user,
            csv_filename=csv_file.name,
            total_rows=len(rows),
            staged_data=rows
        )

        request.session[SESSION_KEY] = str(session.id)
        
        # Extract images if ZIP provided
        if zip_file and zip_file.name.lower().endswith('.zip'):
            try:
                image_map = extract_zip_images(zip_file, session.id)
                session.zip_filename = zip_file.name
                session.image_map = image_map
                session.save()
                
                # Auto-match images
                staged, matched, unmatched = match_images_to_rows(session.staged_data, image_map)
                session.staged_data = staged
                session.matched_images = matched
                session.unmatched_images = unmatched
                session.save()
            except Exception as e:
                messages.error(request, f"Error processing ZIP: {str(e)}")
                
        return redirect('upload:bulk_import_step2')

    return render(request, 'upload/asset/bulk_import/step1.html', {'title': 'Bulk Asset Upload - Step 1'})

@login_required
def bulk_import_step2(request):
    session_id = request.session.get(SESSION_KEY)
    if not session_id:
        return redirect('upload:bulk_import_step1')
        
    session = get_object_or_404(BulkUploadSession, id=session_id, organization=request.user.organization)
    
    if request.method == 'POST':
        # mapping_data is JSON from frontend
        mapping_data_str = request.POST.get('mapping_data')
        if not mapping_data_str:
            messages.error(request, "No mapping data received. Please select products and fields for each row.")
            return redirect('upload:bulk_import_step2')
        mapping_data = json.loads(mapping_data_str)
        apply_dept_location_mapping(session, mapping_data, request.user.organization)
        return redirect('upload:bulk_import_step4')
            
    locations = Location.undeleted_objects.filter(organization=request.user.organization)
    departments = Department.undeleted_objects.filter(organization=request.user.organization)
    products = Product.undeleted_objects.filter(organization=request.user.organization)
    vendors = Vendor.undeleted_objects.filter(organization=request.user.organization)
    clients = Client.undeleted_objects.filter(organization=request.user.organization)
    statuses = AssetStatus.undeleted_objects.filter(
        Q(organization=request.user.organization) | Q(organization__isnull=True)
    )
    
    staged_data_for_template = []
    csv_headers = []
    if session.staged_data:
        exclude_keys = {
            'product_target_id', 'vendor_target_id', 'client_target_id', 
            'location_target_id', 'status_target_id',
            'purchase_type', 'matched_image_path', 'image_status'
        }
        # Define preferred order and display names for known CSV columns
        column_defs = [
            ('serial_no', 'Serial Number'),
            ('asset_name', 'Asset Name'),
            ('name', 'Asset Name'),
            ('tag', 'Tag'),
            ('price', 'Price'),
            ('purchase_date', 'Purchase Date'),
            ('warranty_expiry_date', 'Warranty Expiry'),
            ('description', 'Description'),
            ('image_filename', 'Image File'),
        ]
        available_keys = set(session.staged_data[0].keys()) - exclude_keys
        for key, display in column_defs:
            if key in available_keys:
                csv_headers.append((key, display))
                available_keys.discard(key)

        # Append active custom field columns with their human-readable label
        active_cfs = _get_active_asset_cfs(request.user.organization).values('field_key', 'field_label')
        for cf in active_cfs:
            if cf['field_key'] in available_keys:
                csv_headers.append((cf['field_key'], cf['field_label']))
                available_keys.discard(cf['field_key'])

        # Any remaining unknown keys (passthrough)
        for key in sorted(available_keys):
            csv_headers.append((key, key.replace('_', ' ').title()))

    for i, row in enumerate(session.staged_data):
        csv_values = [row.get(h[0], '') for h in csv_headers]
        staged_data_for_template.append({
            'index': i,
            'row': row,
            'csv_values': csv_values
        })
    
    return render(request, 'upload/asset/bulk_import/step2.html', {
        'title': 'Bulk Asset Upload - Step 2 (Mapping)',
        'session': session,
        'locations': locations,
        'departments': departments,
        'products': products,
        'vendors': vendors,
        'clients': clients,
        'statuses': statuses,
        'csv_headers': csv_headers,
        'staged_data_for_template': staged_data_for_template,
        'image_map': session.image_map,
        'per_page': 15,
    })

@login_required
def bulk_import_step4(request):
    session_id = request.session.get(SESSION_KEY)
    if not session_id:
        return redirect('upload:bulk_import_step1')
        
    session = get_object_or_404(BulkUploadSession, id=session_id, organization=request.user.organization)
    
    if session.status != 'mapped':
        messages.warning(request, "Please complete the mapping step before finalizing.")
        return redirect('upload:bulk_import_step2')
    
    if request.method == 'POST':
        if not request.POST.get('confirm_import'):
            messages.error(request, "Please check the confirmation box.")
            return redirect('upload:bulk_import_step4')
            
        created_count, errors = commit_bulk_session(session, request)
        if errors:
            for err in errors[:10]:
                messages.error(request, err)
            if len(errors) > 10:
                messages.error(request, f"...and {len(errors)-10} more import errors.")
            return redirect('upload:bulk_import_step4')
            
        messages.success(request, f"Successfully imported {created_count} assets!")
        del request.session[SESSION_KEY]
        return redirect('assets:list')
        
    return render(request, 'upload/asset/bulk_import/step4.html', {
        'title': 'Bulk Asset Upload - Step 3 (Finalize)',
        'session': session,
    })

@login_required
def bulk_import_cancel(request):
    session_id = request.session.get(SESSION_KEY)
    if session_id:
        # Delete staged images before removing the session record
        cleanup_bulk_import_files(session_id)
        BulkUploadSession.objects.filter(id=session_id, organization=request.user.organization).delete()
        del request.session[SESSION_KEY]
    messages.info(request, "Bulk import cancelled.")
    return redirect('upload:bulk_import_step1')

@login_required
def download_asset_template_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assets_template.csv"'
    
    writer = csv.writer(response, quoting=csv.QUOTE_ALL)

    # Core fixed columns
    core_headers = [
        'asset_name', 'serial_no', 'tag', 'price', 'purchase_date',
        'warranty_expiry_date', 'description', 'image_filename',
    ]
    core_sample = [
        'MacBook Pro M3 Max 16-inch', 'SN-APL-893011', 'LAP-001', '3499.99',
        '2024-01-15', '2027-01-15', 'Engineering laptop for development team',
        'macbook_pro.jpg',
    ]

    # Fetch active asset custom fields for this organization
    active_cfs = list(_get_active_asset_cfs(request.user.organization))

    cf_headers = [cf.field_key for cf in active_cfs]
    cf_sample  = [_CF_TYPE_SAMPLE.get(cf.field_type, 'Example') for cf in active_cfs]

    writer.writerow(core_headers + cf_headers)
    writer.writerow(core_sample  + cf_sample)

    return response

@login_required
def download_asset_template_zip(request):
    # Dummy zip with just a README for the template
    import zipfile
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('README.txt', 'Put your asset images here (.jpg, .png) and map them in the CSV image_filename column.')
    
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="asset_photos.zip"'
    return response
