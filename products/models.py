import uuid
from django.db import models
from dashboard.models import TimeStampModel, Organization, ProductCategory, ProductType, SoftDeleteModel
import os
from uuid import uuid4
from django_resized import ResizedImageField
from simple_history.models import HistoricalRecords


def path_and_rename(instance, filename):
    upload_to =  'product/'
    ext = filename.split('.')[-1]
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)

class Product(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    product_picture = ResizedImageField(upload_to=path_and_rename, blank=True, null=True)
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    model=models.CharField(max_length=100,  blank=True, null=True)
    eol=models.IntegerField(blank=True,null=True)
    description = models.TextField(blank=True, null=True)
    product_category = models.ForeignKey(ProductCategory, models.DO_NOTHING, blank=True, null=True)
    product_type = models.ForeignKey(ProductType, models.DO_NOTHING, blank=True, null=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=path_and_rename, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)