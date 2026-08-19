import uuid

from django.db import models
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

    class Meta:
        db_table="sensor_threshold"
