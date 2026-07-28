"""
Celery tasks for the upload app.

run_bulk_import
    Processes a BulkUploadSession asynchronously — creates Asset and AssetImage
    records row-by-row using savepoints (partial-success / best-effort strategy).
    Progress is saved to the DB every PROGRESS_SAVE_EVERY rows so the frontend
    progress-banner can poll it without hammering the database.
"""

import os
import logging

from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q

from assets.models import Asset, AssetImage, AssetStatus, Product, Vendor
from clients.models import Client
from configurations.models import TagConfiguration
from configurations.utils import generate_asset_tag
from dashboard.models import Location
from upload.bulk_upload_utils import cleanup_bulk_import_files
from upload.models import BulkUploadSession

logger = logging.getLogger(__name__)

# Save progress to DB after this many rows (keeps DB writes low while still
# giving the frontend meaningful live updates).
PROGRESS_SAVE_EVERY = 25
# Maximum number of per-row error strings kept in the session (prevents the
# import_errors JSONField from growing unbounded).
MAX_STORED_ERRORS = 200


@shared_task(bind=True, max_retries=0)
def run_bulk_import(self, session_id: str, user_id: str) -> dict:
    """
    Background task: commit all staged rows in a BulkUploadSession.

    Failure strategy — PARTIAL SUCCESS (best-effort):
        Each row is wrapped in its own savepoint.  A bad row is rolled back
        individually; all successfully created assets remain committed.
        The caller receives a summary of how many rows succeeded vs failed.

    Args:
        session_id: str(UUID) of the BulkUploadSession to process.
        user_id:    str(UUID) of the User who triggered the import (stored on
                    each created Asset as created_by).

    Returns:
        dict with keys: created, failed, total
    """
    try:
        session = BulkUploadSession.objects.get(id=session_id)
    except BulkUploadSession.DoesNotExist:
        logger.error("run_bulk_import: session %s not found", session_id)
        return {"error": "session_not_found"}

    # ── Mark as processing ────────────────────────────────────────────────
    session.status = "processing"
    session.processed_rows = 0
    session.created_count = 0
    session.import_errors = []
    session.save(update_fields=["status", "processed_rows", "created_count", "import_errors"])

    organization = session.organization
    staged = session.staged_data
    total = len(staged)

    # ── Pre-fetch all FK look-up tables once ─────────────────────────────
    products_by_id  = {str(p.id): p for p in Product.objects.filter(organization=organization)}
    vendors_by_id   = {str(v.id): v for v in Vendor.objects.filter(organization=organization)}
    clients_by_id   = {str(c.id): c for c in Client.objects.filter(organization=organization)}
    locations_by_id = {str(l.id): l for l in Location.objects.filter(organization=organization)}
    statuses_by_id  = {}
    for s in AssetStatus.objects.filter(Q(organization=organization) | Q(organization__isnull=True)):
        statuses_by_id[str(s.id)] = s

    available_status = AssetStatus.objects.filter(
        name__iexact="Available", organization=organization
    ).first()

    existing_tags = set(
        Asset.objects.filter(organization=organization).values_list("tag", flat=True)
    )

    tag_config = TagConfiguration.objects.filter(
        organization=organization, use_default_settings=True
    ).first()

    created_count = 0
    errors: list[str] = []

    # ── Row loop ─────────────────────────────────────────────────────────
    for idx, row in enumerate(staged):
        sid = transaction.savepoint()
        try:
            product  = products_by_id.get(row.get("product_target_id") or "")
            vendor   = vendors_by_id.get(row.get("vendor_target_id") or "")
            client   = clients_by_id.get(row.get("client_target_id") or "")
            location = locations_by_id.get(row.get("location_target_id") or "")

            status_val = available_status
            status_id  = row.get("status_target_id")
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
                created_by=str(user_id),
            )

            img_path = row.get("matched_image_path")
            if img_path:
                abs_img_path = os.path.abspath(img_path)
                if os.path.exists(abs_img_path):
                    with open(abs_img_path, "rb") as f:
                        AssetImage.objects.create(
                            asset=asset,
                            image=ContentFile(f.read(), name=os.path.basename(abs_img_path)),
                        )

            created_count += 1
            transaction.savepoint_commit(sid)

        except Exception as exc:
            transaction.savepoint_rollback(sid)
            error_msg = f"Row {idx + 1} ({row.get('name', '?')}): {exc}"
            logger.warning("run_bulk_import: %s", error_msg)
            if len(errors) < MAX_STORED_ERRORS:
                errors.append(error_msg)

        # ── Periodic progress flush ───────────────────────────────────────
        rows_done = idx + 1
        if rows_done % PROGRESS_SAVE_EVERY == 0 or rows_done == total:
            try:
                session.processed_rows = rows_done
                session.created_count  = created_count
                session.import_errors  = errors
                session.save(update_fields=["processed_rows", "created_count", "import_errors"])
            except Exception as save_exc:
                logger.warning("run_bulk_import: progress save failed: %s", save_exc)

    # ── Finalise ─────────────────────────────────────────────────────────
    final_status = "done"   # done = finished (partial errors are acceptable)
    session.status         = final_status
    session.processed_rows = total
    session.created_count  = created_count
    session.import_errors  = errors
    session.save(update_fields=["status", "processed_rows", "created_count", "import_errors"])

    # Clean up staged image files only when all rows succeeded
    if not errors:
        cleanup_bulk_import_files(session.id)

    logger.info(
        "run_bulk_import: session=%s done — created=%d, failed=%d, total=%d",
        session_id, created_count, len(errors), total,
    )
    return {"created": created_count, "failed": len(errors), "total": total}
