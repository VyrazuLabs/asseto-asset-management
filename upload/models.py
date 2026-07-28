import uuid
from django.db import models
from dashboard.models import Department, Location, TimeStampModel, Organization, Address
import os
from uuid import uuid4

from roles.models import Role


def path_and_rename(instance, filename):
    upload_to = "csv/"
    ext = filename.split(".")[-1]
    if instance.pk:
        filename = "{}.{}".format(instance.pk, ext)
    else:
        filename = "{}.{}".format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)


class Upload(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, models.DO_NOTHING, blank=True, null=True
    )
    entity_type = models.CharField(max_length=255, blank=True, null=True)
    entity_id = models.IntegerField(blank=True, null=True)
    filename = models.CharField(max_length=255, blank=True, null=True)
    orignal_filename = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    size = models.CharField(max_length=255, blank=True, null=True)


class File(models.Model):
    file = models.FileField(upload_to=path_and_rename, blank=True, null=True)


class ImportedUser(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    entity_type = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=12, blank=True, null=True)
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person_email = models.EmailField(max_length=255, blank=True, null=True)
    contact_person_phone = models.CharField(max_length=12, blank=True, null=True)
    address = models.ForeignKey(
        Address, on_delete=models.CASCADE, blank=True, null=True
    )
    organization = models.ForeignKey(
        Organization, models.DO_NOTHING, blank=True, null=True
    )
    gstin_number = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=50, blank=True, null=True)
    department = models.ForeignKey(Department, models.DO_NOTHING, blank=True, null=True)
    office_location = models.ForeignKey(
        Location, models.DO_NOTHING, blank=True, null=True
    )
    role = models.ForeignKey(Role, models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.full_name}"

class BulkUploadSession(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, null=True)
    created_by = models.ForeignKey('authentication.User', on_delete=models.CASCADE, null=True)
    csv_filename = models.CharField(max_length=255, blank=True, null=True)
    zip_filename = models.CharField(max_length=255, blank=True, null=True)
    staged_data = models.JSONField(default=list)   # parsed CSV rows
    image_map = models.JSONField(default=dict)     # {filename: saved_path}
    total_rows = models.IntegerField(default=0)
    matched_images = models.IntegerField(default=0)
    unmatched_images = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='pending',
        choices=[
            ('pending', 'Pending'),
            ('mapped', 'Mapped'),
            ('processing', 'Processing'),   # Celery task is running
            ('done', 'Done'),               # Celery task finished (with or without partial errors)
            ('failed', 'Failed'),           # Celery task crashed entirely
            ('committed', 'Committed'),     # Legacy: synchronous commit (small datasets)
        ])
    # --- Async / Celery tracking ---
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    processed_rows = models.IntegerField(default=0)   # rows attempted so far (for progress)
    created_count  = models.IntegerField(default=0)   # successfully created assets
    import_errors  = models.JSONField(default=list)   # list of per-row error strings

    class Meta:
        verbose_name = "Bulk Upload Session"
        ordering = ['-created_at']
