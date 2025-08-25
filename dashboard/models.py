import uuid
from django.db import models
import os
from uuid import uuid4
from django_resized import ResizedImageField
from simple_history.models import HistoricalRecords


def path_and_rename(instance, filename):
    upload_to =  'logo/'
    ext = filename.split('.')[-1]
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)


class TimeStampModel(models.Model):
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)  
    created_by = models.CharField(max_length=255, blank=True, null=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True
        
        
class RestoreManager(models.Manager):
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=True)


class SoftDeleteManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    
class SoftDeleteModel(models.Model):

    is_deleted = models.BooleanField(default=False)
    objects = models.Manager()
    undeleted_objects = SoftDeleteManager()
    deleted_objects = RestoreManager()

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    class Meta:
        abstract = True


class Department(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person_email = models.CharField(max_length=255, blank=True, null=True)
    contact_person_phone = models.CharField(max_length=255, blank=True, null=True)
    organization = models.ForeignKey('Organization', models.DO_NOTHING, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name    

class Location(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('Organization', models.DO_NOTHING, blank=True, null=True)
    office_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person_name = models.CharField(max_length=255, blank=True, null=True)
    contact_person_email = models.EmailField(max_length=255, blank=True, null=True)
    contact_person_phone = models.CharField(max_length=255, blank=True, null=True)
    address = models.ForeignKey('Address', on_delete=models.CASCADE, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.office_name} - {self.address.address_line_one}'
    

class Organization(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    date_format = models.CharField(max_length=255, blank=True, null=True)
    logo = ResizedImageField(upload_to=path_and_rename, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    

class ProductType(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    can_modify=models.BooleanField(default=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    

class ProductCategory(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    parent=models.ForeignKey('self',related_name='subcategories',on_delete=models.CASCADE, null=True,blank=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        if self.name is None:
            return None
        return self.name


class Address(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address_line_one = models.TextField(blank=True, null=True)
    address_line_two = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    pin_code = models.CharField(max_length=255, blank=True, null=True)

    # def __str__(self):
    #     return f'{self.address_line_one}, {self.address_line_two}, {self.country}, {self.state}, {self.city}, {self.pin_code}'    

class CustomField(models.Model):
    ENTITY_CHOICES = [
        ('asset', 'Asset'),
        ('product', 'Product'),
        ('vendor', 'Vendor'),
    ]
    entity_id=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    object_id=models.UUIDField( default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=30)
    field_name=models.CharField(max_length=255, blank=True, null=True)
    field_value=models.CharField(max_length=255, blank=True, null=True)
    entity_type = models.CharField(max_length=30, choices=ENTITY_CHOICES)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE,null=True,blank=True)
    required = models.BooleanField(default=False)