import uuid
from django.db import models
from dashboard.models import TimeStampModel, Organization,Address
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
class ImportedUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    entity_type=models.CharField(max_length=255 , blank=True, null=True)
    email = models.EmailField(max_length=255)
    username = models.CharField(max_length=255 , blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone=models.CharField(max_length=12,blank=True,null=True)
    contact_person_name=models.CharField(max_length=255, blank=True, null=True)
    contact_person_email = models.EmailField(max_length=255, unique=True)
    contact_person_phone=models.CharField(max_length=12,blank=True,null=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, blank=True, null=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    gstin_number=models.CharField(max_length=255 , blank=True, null=True)
    description=models.CharField(max_length=255 , blank=True, null=True)
    designation=models.CharField(max_length=50 , blank=True, null=True)


    def __str__(self):
        return f'{self.full_name}'

