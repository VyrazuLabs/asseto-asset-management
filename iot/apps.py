from django.apps import AppConfig

from iot.streaming import start_device_heartbeat_stream, start_sensor_stream


class IotSensorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "iot"

    def ready(self):
        from .mqtt_client import start_mqtt
        start_mqtt()
        start_sensor_stream()
        start_device_heartbeat_stream()
