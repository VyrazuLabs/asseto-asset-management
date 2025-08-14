import uuid
from django.db import models
from dashboard.models import TimeStampModel, Organization, SoftDeleteModel, Address
from simple_history.models import HistoricalRecords
# Create your models here.


class Vendor(TimeStampModel, SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=45, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    gstin_number = models.CharField(max_length=45, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    address = models.ForeignKey(
        Address, on_delete=models.CASCADE, blank=True, null=True)
    organization = models.ForeignKey(
        Organization, models.DO_NOTHING, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name
