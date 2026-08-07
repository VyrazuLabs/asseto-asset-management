from pandas import errors
import csv
import os
import re
import shutil
import zipfile
from datetime import datetime

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_save

from assets.models import Asset, AssetImage, AssetStatus, Product, Vendor
from clients.models import Client
from configurations.models import TagConfiguration
from configurations.utils import generate_asset_tag
from custom_fields.models import CustomFieldDefinition, CustomFieldValue
from dashboard.models import Location
from notifications.signals import notify_admin_on_asset_created


# ---------------------------------------------------------------------------
# Custom Field Helpers
# ---------------------------------------------------------------------------

def _get_active_asset_cfs(organization):
    """
    Return all active, non-deleted asset CustomFieldDefinition objects for the
    given organization, ordered by field_label.
    """
    if organization is None:
        return CustomFieldDefinition.objects.none()
    return CustomFieldDefinition.objects.filter(
        organization=organization,
        module="asset",
        is_active=True,
        is_deleted=False,
    ).order_by("field_label")


def validate_and_normalize_cf_value(value, field_type, field_label, row_num):
    """
    Validate *value* against *field_type* and return a (normalized_value, error)
    tuple.  On success error is None; on failure normalized_value is None.
    """
    v = value.strip()
    if not v:
        # Empty optional value — nothing to validate
        return "", None

    if field_type == "text":
        return v, None

    elif field_type == "integer":
        try:
            return str(int(v)), None
        except ValueError:
            return None, f"Row {row_num}: '{field_label}' must be an integer (e.g. 5)."

    elif field_type == "decimal":
        try:
            return str(float(v)), None
        except ValueError:
            return None, f"Row {row_num}: '{field_label}' must be a decimal number (e.g. 99.99)."

    elif field_type == "date":
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(v, fmt).strftime("%Y-%m-%d"), None
            except ValueError:
                pass
        return None, f"Row {row_num}: '{field_label}' has an invalid date format (use YYYY-MM-DD)."

    elif field_type == "boolean":
        if v.lower() in ("yes", "true", "1"):
            return "true", None
        elif v.lower() in ("no", "false", "0"):
            return "false", None
        return None, f"Row {row_num}: '{field_label}' must be Yes/No or True/False."

    elif field_type == "email":
        if re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            return v, None
        return None, f"Row {row_num}: '{field_label}' is not a valid email address."

    # Unknown type — pass through
    return v, None


# ---------------------------------------------------------------------------
# CSV Parsing
# ---------------------------------------------------------------------------

def parse_csv_file(csv_file, organization=None):
    rows = []
    errors = []
    try:
        # csv_file is an InMemoryUploadedFile
        decoded_file = csv_file.read().decode("utf-8-sig").splitlines()
        reader = csv.DictReader(decoded_file)

        # ------------------------------------------------------------------
        # 1. Header-level validation
        # ------------------------------------------------------------------
        if reader.fieldnames:
            expected_headers = {
                "asset_name",
                "serial_no",
                "tag",
                "price",
                "purchase_date",
                "warranty_expiry_date",
                "description",
                "image_filename",
            }
            actual_headers = {h.strip() for h in reader.fieldnames if h}

            if "asset name" in actual_headers:
                actual_headers.add("asset_name")

            # Core columns must be present
            missing_headers = expected_headers - actual_headers
            if missing_headers:
                missing_str = ", ".join(sorted(missing_headers))
                errors.append(
                    f"Invalid CSV Header: Missing expected column(s): {missing_str}. Please use the provided template."
                )
                return [], errors

            # ------------------------------------------------------------------
            # 2. Custom field: file-level required column check
            # ------------------------------------------------------------------
            # Build maps of all active CFs and required CFs
            active_cf_map = {}   # field_key -> CustomFieldDefinition
            required_cf_map = {}  # field_key -> field_label (only is_required=True)

            if organization:
                for cf in _get_active_asset_cfs(organization):
                    active_cf_map[cf.field_key] = cf
                    if cf.is_required:
                        required_cf_map[cf.field_key] = cf.field_label

            for key, label in required_cf_map.items():
                if key not in actual_headers:
                    errors.append(
                        f"Missing required column '{key}' ({label}). "
                        f"This is a required custom field — please use the latest template."
                    )

            if errors:
                return [], errors

        else:
            active_cf_map = {}
            required_cf_map = {}

        # ------------------------------------------------------------------
        # 3. Row-level validation
        # ------------------------------------------------------------------
        for idx, row in enumerate(reader):
            row_num = idx + 1

            # Clean row dict keys and values
            clean_row = {k.strip(): v.strip() if v else "" for k, v in row.items() if k}

            # Normalize 'asset name' column to 'name' for internal processing
            if "asset_name" in clean_row and "name" not in clean_row:
                clean_row["name"] = clean_row.pop("asset_name")
            elif "asset name" in clean_row and "name" not in clean_row:
                clean_row["name"] = clean_row.pop("asset name")

            # Required core field
            if not clean_row.get("name"):
                errors.append(f"Row {row_num}: 'asset_name' (or 'name') is required.")
                continue

            # Date validation and normalization (core columns)
            for date_col in ["purchase_date", "warranty_expiry_date"]:
                date_val = clean_row.get(date_col)
                if date_val:
                    parsed_date = None
                    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                        try:
                            parsed_date = datetime.strptime(date_val, fmt).date()
                            break
                        except ValueError:
                            pass
                    if not parsed_date:
                        errors.append(f"Row {row_num}: invalid {date_col} format.")
                    else:
                        clean_row[date_col] = parsed_date.strftime("%Y-%m-%d")

            # Normalize purchase type
            p_type = clean_row.get("purchase_type", "").lower()
            if "own" in p_type:
                clean_row["purchase_type"] = "1"
            elif "rent" in p_type:
                clean_row["purchase_type"] = "2"
            else:
                clean_row["purchase_type"] = ""

            # ------------------------------------------------------------------
            # Custom field: row-level required + type validation
            # ------------------------------------------------------------------
            row_has_cf_error = False

            for cf_key, cf_def in active_cf_map.items():
                raw_val = clean_row.get(cf_key, "")

                # Required check (row-level)
                if cf_def.is_required and not raw_val:
                    errors.append(
                        f"Row {row_num}: '{cf_def.field_label}' is a required custom field and cannot be empty."
                    )
                    row_has_cf_error = True
                    continue

                # Field type validation + normalization (skip empty optional values)
                if raw_val:
                    normalized, err = validate_and_normalize_cf_value(
                        raw_val, cf_def.field_type, cf_def.field_label, row_num
                    )
                    if err:
                        errors.append(err)
                        row_has_cf_error = True
                    else:
                        clean_row[cf_key] = normalized

            if row_has_cf_error:
                # Don't append the row — but keep collecting errors for other rows
                continue

            rows.append(clean_row)

    except Exception as e:
        errors.append(f"Error parsing CSV: {str(e)}")

    # If there are any errors (including row-level), reject the entire file
    if errors:
        return [], errors

    return rows, errors


def cleanup_bulk_import_files(session_id):
    """
    Delete the temporary directory that holds staged images for a bulk import
    session.  Safe to call even if the directory does not exist.
    """
    staging_dir = os.path.join("media", "bulk_import", str(session_id))
    if os.path.isdir(staging_dir):
        shutil.rmtree(staging_dir, ignore_errors=True)


def extract_zip_images(zip_file, session_id):
    image_map = {}
    allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    relative_dir = os.path.join("media", "bulk_import", str(session_id))
    abs_extract_dir = os.path.abspath(relative_dir)
    os.makedirs(abs_extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_file, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue

            filename = os.path.basename(info.filename)
            if not filename:
                continue
            ext = os.path.splitext(filename)[1].lower()

            if ext in allowed_exts:
                target_abs_path = os.path.abspath(
                    os.path.join(abs_extract_dir, filename)
                )
                if not target_abs_path.startswith(abs_extract_dir):
                    continue
                with z.open(info) as source, open(target_abs_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                image_map[filename.lower()] = os.path.join(relative_dir, filename)

    return image_map


def match_images_to_rows(staged_data, image_map):
    matched = 0
    unmatched = 0

    for row in staged_data:
        img_file = row.get("image_filename", "").lower().strip()
        if img_file and img_file in image_map:
            row["matched_image_path"] = image_map[img_file]
            row["image_status"] = "matched"
            matched += 1
        elif img_file:
            row["image_status"] = "missing"
            unmatched += 1
        else:
            row["image_status"] = "none"

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
            row["product_target_id"] = m.get("product_id")
            row["vendor_target_id"] = m.get("vendor_id")
            row["client_target_id"] = m.get("client_id")
            row["location_target_id"] = m.get("location_id")
            row["status_target_id"] = m.get("status_id")
            row["purchase_type"] = m.get("purchase_type") or row.get(
                "purchase_type", ""
            )

            # Handle image_path from modal selection
            image_path = m.get("image_path")
            if image_path and image_path.strip():
                row["matched_image_path"] = image_path.strip()
                row["image_status"] = "matched"
            elif "image_path" in m:
                # Explicitly cleared by user — remove any previous image
                row.pop("matched_image_path", None)
                img_file = row.get("image_filename", "").lower().strip()
                if img_file:
                    row["image_status"] = "missing"
                else:
                    row["image_status"] = "none"

    session.staged_data = staged
    session.status = "mapped"
    session.save()


@transaction.atomic
def commit_bulk_session(session, request):
    created_count = 0
    errors = []

    organization = session.organization
    staged = session.staged_data

    available_status = AssetStatus.objects.filter(
        name__iexact="Available", organization=organization
    ).first()

    # Pre-fetch all FK data once before the loop
    products_by_id = {
        str(p.id): p for p in Product.objects.filter(organization=organization)
    }
    vendors_by_id = {
        str(v.id): v for v in Vendor.objects.filter(organization=organization)
    }
    clients_by_id = {
        str(c.id): c for c in Client.objects.filter(organization=organization)
    }
    locations_by_id = {
        str(l.id): l for l in Location.objects.filter(organization=organization)
    }
    statuses_by_id = {}
    for s in AssetStatus.objects.filter(
        Q(organization=organization) | Q(organization__isnull=True)
    ):
        statuses_by_id[str(s.id)] = s
    existing_tags = set(
        Asset.objects.filter(organization=organization).values_list("tag", flat=True)
    )

    tag_config = TagConfiguration.objects.filter(
        organization=organization, use_default_settings=True
    ).first()

    # Pre-fetch active asset custom fields once (outside the loop)
    active_cf_map = {
        cf.field_key: cf
        for cf in _get_active_asset_cfs(organization)
    }

    for idx, row in enumerate(staged):
        sid = transaction.savepoint()
        try:
            prod_id = row.get("product_target_id")
            product = products_by_id.get(prod_id) if prod_id else None

            vend_id = row.get("vendor_target_id")
            vendor = vendors_by_id.get(vend_id) if vend_id else None

            cli_id = row.get("client_target_id")
            client = clients_by_id.get(cli_id) if cli_id else None

            loc_id = row.get("location_target_id")
            location = locations_by_id.get(loc_id) if loc_id else None

            status_val = available_status
            status_id = row.get("status_target_id")
            if status_id:
                status_val = statuses_by_id.get(status_id) or available_status

            tag = row.get("tag")
            if not tag:
                if tag_config:
                    tag = generate_asset_tag(
                        prefix=tag_config.prefix,
                        number_suffix=tag_config.number_suffix,
                    )
                else:
                    tag = generate_asset_tag(prefix="VY", number_suffix="001")

            if tag in existing_tags:
                raise ValueError(f"Asset tag '{tag}' already exists. Tags must be unique.")
            existing_tags.add(tag)

            asset = Asset.objects.create(
                organization=organization,
                name=row.get("name"),
                serial_no=row.get("serial_no"),
                tag=tag,
                price=float(row.get("price")) if row.get("price") else None,
                purchase_date=row.get("purchase_date") or None,
                warranty_expiry_date=row.get("warranty_expiry_date") or None,
                purchase_type=row.get("purchase_type"),
                description=row.get("description"),
                product=product,
                vendor=vendor,
                client=client,
                location=location,
                asset_status=status_val,
                created_by=str(request.user.id),
            )

            # ------------------------------------------------------------------
            # Save custom field values for this asset
            # ------------------------------------------------------------------
            for cf_key, cf_def in active_cf_map.items():
                value = row.get(cf_key, "")
                if value:
                    CustomFieldValue.objects.update_or_create(
                        definition=cf_def,
                        entity_uuid=asset.id,
                        defaults={"value_text": value},
                    )

            img_path = row.get("matched_image_path")
            if img_path:
                abs_img_path = os.path.abspath(img_path)
                if os.path.exists(abs_img_path):
                    with open(abs_img_path, "rb") as f:
                        AssetImage.objects.create(
                            asset=asset,
                            image=ContentFile(
                                f.read(), name=os.path.basename(abs_img_path)
                            ),
                        )

            created_count += 1
            transaction.savepoint_commit(sid)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            errors.append(f"Row {idx + 1} ({row.get('name')}): {str(e)}")

    if not errors:
        cleanup_bulk_import_files(session.id)
        session.delete()

    return created_count, errors
