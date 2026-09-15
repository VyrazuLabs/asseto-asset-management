import uuid
import os
from uuid import uuid4
from django.db import models
from dashboard.models import TimeStampModel, Organization, Location, SoftDeleteModel
from products.models import Product
from vendors.models import Vendor
from simple_history.models import HistoricalRecords
from django_resized import ResizedImageField
from django.conf import settings


def consumable_image_path(instance, filename):
    upload_to = "consumables/"
    ext = filename.split(".")[-1]
    if instance.pk:
        filename = "{}.{}".format(instance.pk, ext)
    else:
        filename = "{}.{}".format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)


class Consumable(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consumable_name = models.CharField(max_length=255, blank=True, null=True)
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, blank=True, null=True, related_name="consumables"
    )
    vendor = models.ForeignKey(
        Vendor, on_delete=models.SET_NULL, blank=True, null=True, related_name="consumables"
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, blank=True, null=True
    )
    item_no = models.CharField(max_length=255, blank=True, null=True)
    order_number = models.CharField(max_length=255, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    remaining_quantity = models.IntegerField(blank=True, null=True)
    min_qty = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    image = ResizedImageField(upload_to=consumable_image_path, blank=True, null=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.SET_NULL, blank=True, null=True
    )
    history = HistoricalRecords()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.consumable_name or "Consumable"

    def save(self, *args, **kwargs):
        if self.remaining_quantity is None and self.quantity is not None:
            self.remaining_quantity = self.quantity
        super().save(*args, **kwargs)

    def is_low_stock(self):
        qty = self.remaining_quantity if self.remaining_quantity is not None else self.quantity
        if qty is not None and self.min_qty is not None:
            return qty <= self.min_qty
        return False

class ConsumableCheckout(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consumable = models.ForeignKey(Consumable, on_delete=models.CASCADE, related_name="checkouts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consumable_checkouts")
    quantity = models.IntegerField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.consumable} - {self.user} - {self.quantity}"
