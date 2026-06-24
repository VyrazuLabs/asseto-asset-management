import uuid, os
from django.db import models
from dashboard.models import Location, TimeStampModel, Organization, SoftDeleteModel
from products.models import Product
from vendors.models import Vendor
from django.db.models import Sum
from authentication.models import User
from simple_history.models import HistoricalRecords


from clients.models import Client


def path_and_rename(instance, filename):
    upload_to = "asset_images/"
    ext = filename.split(".")[-1]
    if instance.pk:
        filename = "{}.{}".format(instance.pk, ext)
    else:
        filename = "{}.{}".format(uuid.uuid4().hex, ext)
    return os.path.join(upload_to, filename)


class AssetSpecification(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey("Asset", models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Asset Specification"
        verbose_name_plural = "Asset Specifications"
        ordering = ["-created_at"]


class AssetStatus(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    can_modify = models.BooleanField(default=True)
    organization = models.ForeignKey(
        Organization, models.DO_NOTHING, blank=True, null=True
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Asset Status"
        verbose_name_plural = "Asset Statuses"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class AssetStatusChoice(models.IntegerChoices):
    ASSIGNED = 0, "Assigned"
    AVAILABLE = 1, "Available"
    REPAIR_REQUIRED = 2, "Repair Required"
    LOST_STOLEN = 3, "Lost/Stolen"
    BROKEN = 4, "Broken"
    READY_TO_DEPLOY = 5, "Ready To Deploy"
    OUT_FOR_REPAIR = 6, "Out for Repair"


class Asset(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.IntegerField(
        choices=AssetStatusChoice.choices, default=AssetStatusChoice.AVAILABLE
    )
    tag = models.CharField(max_length=255, blank=False, null=True, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    serial_no = models.CharField(max_length=45, blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    asset_status = models.ForeignKey(
        AssetStatus, models.DO_NOTHING, null=True, blank=True
    )
    purchase_date = models.DateField(blank=True, null=True)
    warranty_expiry_date = models.DateField(blank=True, null=True)
    purchase_type = models.CharField(max_length=45, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_assigned = models.BooleanField(default=False)
    product = models.ForeignKey(Product, models.PROTECT, blank=True, null=True)
    vendor = models.ForeignKey(Vendor, models.PROTECT, blank=True, null=True)
    client = models.ForeignKey(
        "clients.Client",
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="assets",
    )
    location = models.ForeignKey(Location, models.DO_NOTHING, blank=True, null=True)
    organization = models.ForeignKey(
        Organization, models.DO_NOTHING, blank=True, null=True
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        ordering = ["-created_at"]

    def get_status(self):
        return AssetStatusChoice(self.status).label

    def __str__(self):
        return self.name


class AssetImage(models.Model):
    asset = models.ForeignKey("Asset", on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=path_and_rename, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asset Image"
        verbose_name_plural = "Asset Images"
        ordering = ["-uploaded_at"]

    def __str__(self):
        if self.image and hasattr(self.image, "url"):
            return str(self.image.url)
        return "No Image"


class AssignAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True)
    assigned_date = models.DateField(auto_now_add=True, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Assign Asset"
        verbose_name_plural = "Assign Assets"
        ordering = ["-assigned_date"]

class MaintenanceRecord(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_records')
    service_id = models.CharField(max_length=20, unique=True)
    date = models.DateField()
    maintenance_type = models.CharField(max_length=100) # Calibration, Breakdown, etc.
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    technician = models.CharField(max_length=255)
    status = models.CharField(max_length=50) # Completed, Scheduled, etc.
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Maintenance Record"
        verbose_name_plural = "Maintenance Records"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.service_id} - {self.asset.name}"
