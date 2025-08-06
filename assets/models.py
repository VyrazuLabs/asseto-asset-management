import uuid
from django.db import models
from dashboard.models import Location, TimeStampModel, Organization, SoftDeleteModel
from products.models import Product
from vendors.models import Vendor
from django.db.models import Sum
from authentication.models import User
from simple_history.models import HistoricalRecords

# Create your models here.

class AssetSpecification(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey('Asset', models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)


class Asset(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    serial_no = models.CharField(max_length=45, blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
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

    @classmethod
    def total_asset_cost(self):
        return self.objects.all().aggregate(total_cost=Sum('price')).get('total_cost',0)

    def __str__(self):
        return f'{self.name} ({self.serial_no})'


class AssignAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)