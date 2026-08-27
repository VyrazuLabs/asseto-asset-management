import uuid

from django.db import models
from simple_history.models import HistoricalRecords

from assets.models import Asset
from dashboard.models import Organization, SoftDeleteModel, TimeStampModel


class Device(TimeStampModel, SoftDeleteModel):
    class PairingChoice(models.IntegerChoices):
        UNPAIRED= 0, "unpaired"
        PAIRING= 1, "pairing"
        PAIRED= 2, "paired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)
    device_sn = models.CharField(max_length=255)
    device_token = models.CharField(max_length=255)
    is_paired = models.BooleanField(choices=PairingChoice.choices, default=PairingChoice.UNPAIRED)
    asset = models.ForeignKey(Asset, on_delete=models.DO_NOTHING, related_name="asset")
    history = HistoricalRecords()

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "device"

class DeviceAttachments(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization=models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    attahed_part=models.CharField(max_length=255)
    device=models.ForeignKey(Device, on_delete=models.CASCADE, related_name="device_attachments")
    mqtt_topic = models.CharField(max_length=500, unique=True)
    is_enable=models.BooleanField(default=False)
    history=HistoricalRecords()

    class Meta:
        db_table= "device_attachments"

