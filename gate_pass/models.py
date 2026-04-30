from dashboard.models import TimeStampModel
from django.db import models
from assets.models import Asset
from vendors.models import Vendor
from authentication.models import User
import uuid

class GatePass(TimeStampModel):
    STATUS_CHOICES=[(0,'Pending'),(1,'Approved'),(2,'Draft'),(3,'Rejected'),]
    MOVEMENT_CHOICES=[(0,'Outward'),(1,'Inward')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset=models.ForeignKey(Asset,models.DO_NOTHING)					 
    destination_vendor=models.ForeignKey(Vendor,models.DO_NOTHING)
    movement_type=models.IntegerField(choices=MOVEMENT_CHOICES, default=0)
    expected_return_date=models.DateField(blank=True, null=True)
    purpose_of_movement=models.CharField(max_length=200, blank=True, null=True)
    raised_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        related_name='gatepasses_raised',
        null=True,
        blank=True
    )
    authorised_by = models.ForeignKey(
        User,
        models.DO_NOTHING,
        related_name='gatepasses_authorised',
        null=True,
        blank=True
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
 
 
# Ui seems to display asset_name,asset_id,product_category and cost($) which we can get from the asset by keeping it as a foreignkey here.
# Currently the Status, Raised By and Authorized By is not present in the Add Gate Pass page we need to add it.
 