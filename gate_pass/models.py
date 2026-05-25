from dashboard.models import TimeStampModel, Organization
from django.db import models
from assets.models import Asset
from vendors.models import Vendor
from authentication.models import User
import uuid


class GatePass(TimeStampModel):
    """Tracks asset movements (inward/outward) requiring authorization."""

    STATUS_CHOICES = [(0, 'Pending'), (1, 'Approved'), (2, 'Draft'), (3, 'Rejected')]
    MOVEMENT_CHOICES = [(0, 'Outward'), (1, 'Inward')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, models.PROTECT, null=True, blank=True)
    asset = models.ForeignKey(Asset, models.PROTECT)
    destination_vendor = models.ForeignKey(Vendor, models.PROTECT)
    movement_type = models.IntegerField(choices=MOVEMENT_CHOICES, default=0)
    expected_return_date = models.DateField(blank=True, null=True)
    purpose_of_movement = models.CharField(max_length=200, blank=True, null=True)
    raised_by = models.ForeignKey(
        User,
        models.SET_NULL,
        related_name='gatepasses_raised',
        null=True,
        blank=True,
    )
    authorised_by = models.ForeignKey(
        User,
        models.SET_NULL,
        related_name='gatepasses_authorised',
        null=True,
        blank=True,
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
