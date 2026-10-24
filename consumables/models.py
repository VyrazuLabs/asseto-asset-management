import uuid
import os
from uuid import uuid4
from django.db import models, transaction
from django.db.models import Max, Q
from dashboard.models import TimeStampModel, Organization, Location, SoftDeleteModel
from products.models import Product
from vendors.models import Vendor
from simple_history.models import HistoricalRecords
from django_resized import ResizedImageField
from django.conf import settings


def consumable_image_path(instance, filename):
    """Build the upload path for a Consumable's image, keyed by pk once assigned."""
    upload_to = "consumables/"
    ext = filename.split(".")[-1]
    if instance.pk:
        filename = "{}.{}".format(instance.pk, ext)
    else:
        filename = "{}.{}".format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)


CONSUMABLE_ID_START = 100000


class Consumable(TimeStampModel, SoftDeleteModel):
    """A tracked consumable stock item: purchase details, current/remaining quantity, and a min-qty low-stock threshold."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consumable_id = models.PositiveIntegerField(
        blank=True, null=True, editable=False, db_index=True
    )
    is_serialized = models.BooleanField(default=False)
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
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "consumable_id"],
                name="unique_consumable_id_per_organization",
            )
        ]

    def __str__(self):
        return self.consumable_name or "Consumable"

    @classmethod
    def next_consumable_id(cls, organization):
        """
        Return the next sequential consumable_id for an organization.

        Soft-deleted rows are included so an id is never reused after a
        delete/restore. Callers must hold a lock on the organization row
        (see save()) to keep concurrent creates from colliding.

        Args:
            organization: Organization the sequence belongs to (or None).

        Returns:
            int: One above the highest existing id, or CONSUMABLE_ID_START.
        """
        highest = cls.objects.filter(organization=organization).aggregate(
            highest=Max("consumable_id")
        )["highest"]
        return CONSUMABLE_ID_START if highest is None else highest + 1

    def save(self, *args, **kwargs):
        """Default remaining_quantity to quantity and assign consumable_id on first save, then save as normal."""
        if self.remaining_quantity is None and self.quantity is not None:
            self.remaining_quantity = self.quantity
        if self.consumable_id is None:
            with transaction.atomic():
                if self.organization_id:
                    # Serialise id allocation per organization.
                    Organization.objects.select_for_update().get(pk=self.organization_id)
                self.consumable_id = self.next_consumable_id(self.organization)
                super().save(*args, **kwargs)
            return
        super().save(*args, **kwargs)

    def sync_quantities(self):
        """
        Recompute quantity and remaining_quantity from this consumable's units.

        quantity counts units still owned (not lost/disposed); remaining counts
        those in stock. No-op for non-serialized consumables.
        """
        if not self.is_serialized:
            return
        owned = self.units.exclude(status__in=ConsumableUnit.RETIRED_STATUSES)
        self.quantity = owned.count()
        self.remaining_quantity = owned.filter(status=ConsumableUnit.STATUS_IN_STOCK).count()
        self.save(update_fields=["quantity", "remaining_quantity"])

    def add_units(self, count):
        """
        Create ``count`` new units continuing the existing sequence, then resync quantities.

        Args:
            count: Number of units to add (<= 0 is a no-op).
        """
        if count <= 0:
            return
        with transaction.atomic():
            # Serialise sequence allocation so concurrent restocks cannot collide.
            Consumable.objects.select_for_update().get(pk=self.pk)
            highest = self.units.aggregate(highest=Max("sequence"))["highest"] or 0
            ConsumableUnit.objects.bulk_create(
                ConsumableUnit(consumable=self, sequence=highest + offset)
                for offset in range(1, count + 1)
            )
            self.sync_quantities()

    def apply_serialized_quantity(self):
        """
        Reconcile units with the quantity entered on the form.

        A higher quantity adds units; an equal or lower one just resyncs (the
        form blocks decreases). No-op for non-serialized consumables.
        """
        if not self.is_serialized:
            return
        owned = self.units.exclude(status__in=ConsumableUnit.RETIRED_STATUSES).count()
        target = self.quantity or 0
        if target > owned:
            self.add_units(target - owned)
        else:
            self.sync_quantities()

    def is_low_stock(self):
        """Return True if remaining (or total) quantity is at or below min_qty."""
        qty = self.remaining_quantity if self.remaining_quantity is not None else self.quantity
        if qty is not None and self.min_qty is not None:
            return qty <= self.min_qty
        return False

    @property
    def total_checked_out(self):
        """Return the total quantity checked out."""
        qty = self.quantity or 0
        rem = self.remaining_quantity if self.remaining_quantity is not None else qty
        return max(0, qty - rem)

class ConsumableCheckout(TimeStampModel):
    """A record of a quantity of a Consumable checked out to a user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consumable = models.ForeignKey(Consumable, on_delete=models.CASCADE, related_name="checkouts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consumable_checkouts")
    quantity = models.IntegerField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.consumable} - {self.user} - {self.quantity}"


class ConsumableUnit(TimeStampModel):
    """One individually tagged unit of a serialized Consumable, addressed as ``#<consumable_id>-<sequence>``."""

    STATUS_IN_STOCK = "in_stock"
    STATUS_CHECKED_OUT = "checked_out"
    STATUS_LOST = "lost"
    STATUS_DISPOSED = "disposed"
    STATUS_CHOICES = [
        (STATUS_IN_STOCK, "In Stock"),
        (STATUS_CHECKED_OUT, "Checked Out"),
        (STATUS_LOST, "Lost"),
        (STATUS_DISPOSED, "Disposed"),
    ]
    RETIRED_STATUSES = (STATUS_LOST, STATUS_DISPOSED)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consumable = models.ForeignKey(Consumable, on_delete=models.CASCADE, related_name="units")
    sequence = models.PositiveIntegerField()
    serial_no = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_STOCK)
    checkout = models.ForeignKey(
        ConsumableCheckout, on_delete=models.SET_NULL, blank=True, null=True, related_name="units"
    )

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["consumable", "sequence"], name="unique_unit_sequence_per_consumable"
            ),
            models.UniqueConstraint(
                fields=["consumable", "serial_no"],
                condition=Q(serial_no__isnull=False),
                name="unique_unit_serial_per_consumable",
            ),
        ]

    def __str__(self):
        return self.sub_id

    @property
    def sub_id(self):
        """Return the display id, e.g. ``#100000-03``."""
        return f"#{self.consumable.consumable_id}-{self.sequence:02d}"


def consumable_document_path(instance, filename):
    upload_to = "consumable_documents/"
    ext = filename.split(".")[-1]
    filename = "{}.{}".format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)


class ConsumableDocument(TimeStampModel):
    """A document (bill, receipt, etc.) attached to a Consumable."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    consumable = models.ForeignKey(Consumable, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to=consumable_document_path)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.file_name
