import uuid
from django.db import models
from dashboard.models import TimeStampModel, Organization
import os
from uuid import uuid4


def path_and_rename(instance, filename):
    upload_to = 'csv/'
    ext = filename.split('.')[-1]
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)


class Upload(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, models.DO_NOTHING, blank=True, null=True)
    entity_type = models.CharField(max_length=255, blank=True, null=True)
    entity_id = models.IntegerField(blank=True, null=True)
    filename = models.CharField(max_length=255, blank=True, null=True)
    orignal_filename = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    size = models.CharField(max_length=255, blank=True, null=True)


class File(models.Model):
    file = models.FileField(upload_to=path_and_rename, blank=True, null=True)
