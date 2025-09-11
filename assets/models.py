import uuid, os
from django.db import models
from dashboard.models import Location, TimeStampModel, Organization, SoftDeleteModel
from products.models import Product
from vendors.models import Vendor
from django.db.models import Sum
from authentication.models import User
from simple_history.models import HistoricalRecords


def path_and_rename(instance, filename):
    upload_to = 'asset_images/'
    ext = filename.split('.')[-1]
    if instance.pk:
        filename = '{}.{}'.format(instance.pk, ext)
    else:
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
    return os.path.join(upload_to, filename)

class AssetSpecification(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey('Asset', models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)

class AssetStatus(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    can_modify=models.BooleanField(default=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

class Asset(TimeStampModel, SoftDeleteModel):
    STATUS_CHOICES = [
        (0, 'Assigned'),
        (1, 'Available'),
        (2, 'Repair Required'),
        (3, 'Lost/Stolen'),
        (4, 'Broken'),
        (5, 'Ready To Deploy'),
        (6, 'Out for Repair')
    ]
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.CharField(max_length=255, blank=False, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    serial_no = models.CharField(max_length=45, blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    asset_status=models.ForeignKey(AssetStatus, models.DO_NOTHING, null=True, blank=True)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry_date = models.DateField(blank=True, null=True)
    purchase_type = models.CharField(max_length=45, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_assigned = models.BooleanField(default=False)
    product = models.ForeignKey(Product, models.PROTECT, blank=True, null=True)
    vendor = models.ForeignKey(Vendor, models.PROTECT, blank=True, null=True)
    location = models.ForeignKey(Location, models.DO_NOTHING, blank=True, null=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

class AssetImage(models.Model):
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=path_and_rename, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f"Image for {self.asset.name or self.asset.id}"
    # @classmethod
    # def total_asset_cost(self):
    #     return self.objects.all().aggregate(total_cost=Sum('price')).get('total_cost',0)

    # def __str__(self):
    #     return f'{self.name} ({self.serial_no})'

class AssignAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)                          
    assigned_date = models.DateField(auto_now_add=True,blank=True, null=True)
