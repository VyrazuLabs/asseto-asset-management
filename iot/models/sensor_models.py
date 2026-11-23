import uuid

from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords

from assets.models import Asset
from dashboard.models import Organization, SoftDeleteModel, TimeStampModel
from iot.models.device_models import Device

class Sensor(TimeStampModel, SoftDeleteModel):
    class SensorType(models.TextChoices):
        TEMPERATURE = "temperature", "Temperature"
        HUMIDITY = "humidity", "Humidity"
        VIBRATION = "vibration", "Vibration / Shock"
        POWER = "power", "Power Consumption"
        VOLTAGE = "voltage", "Voltage"
        CURRENT = "current", "Current"
        GPS_LAT = "gps_lat", "GPS Latitude"
        GPS_LNG = "gps_lng", "GPS Longitude"
        PRESSURE = "pressure", "Pressure"
        FLOW_RATE = "flow_rate", "Flow Rate"
        RUNTIME_HRS = "runtime_hrs", "Runtime Hours"
        SOUND = "sound", "Sound"

    class PairingChoice(models.IntegerChoices):
        UNPAIRED= 0, "unpaired"
        PAIRING= 1, "pairing"
        PAIRED= 2, "paired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="device")
    sensor_type = models.CharField(max_length=80, choices=SensorType.choices)
    unit = models.CharField(max_length=50)
    mqtt_topic = models.CharField(max_length=500, unique=True)
    is_paired = models.BooleanField(choices=PairingChoice.choices, default=PairingChoice.UNPAIRED)
    history = HistoricalRecords()

    class Meta:
        db_table="sensor"

    def __str__(self):
        return self.name
        
class SensorThreshold(TimeStampModel):
    OPERATOR_CHOICES = [
        ("gt", "Greater Than"),
        ("lt", "Less Than"),
        ("eq", "Equal To"),
        ("neq", "Not Equal To"),
    ]
    SEVERITY_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]
    sensor = models.ForeignKey(
        Sensor, on_delete=models.CASCADE, related_name="thresholds"
    )
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES)
    value = models.FloatField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    alert_type = models.CharField(max_length=255, default="General Alarm")


    class Meta:
        db_table="sensor_threshold"

class SensorAlarm(TimeStampModel):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("acknowledged", "Acknowledged"),
        ("resolved", "Resolved"),
    ]
    rule = models.ForeignKey(SensorThreshold, on_delete=models.CASCADE, related_name="alarms")
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="alarms")
    triggered_value = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alarms')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alarms')
    resolved_at = models.DateTimeField(null=True, blank=True)
    # Link to support ticket created for this alarm
    ticket = models.ForeignKey(
        "support.SupportTicket",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alarms",
    )

    class Meta:
        db_table="sensor_alarm"
        ordering = ['-created_at']


class SesnorData(models.Model):
    id = models.AutoField(primary_key=True)
    sensor_id = models.CharField(max_length=255, null=False)
    value = models.FloatField(null=False)
    timestamp=models.DateTimeField(null=False)  # the actual numeric reading
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    class Meta:
        db_table = "sensor_data"
        ordering = ["-timestamp"]
