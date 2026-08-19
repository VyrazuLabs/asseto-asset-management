from django.urls import path

from iot.views.iot_device_views import add_device, devices_list
from iot.views.iot_sensors_views import create_sensor_device, sensors_list, check_sensor_heartbeat

app_name = "iot"

urlpatterns = [
    # -------------------------- Sesnors Urls----------------------------#
    path("create-sensor", create_sensor_device, name="add_sensor"),
    path("sensors-list", sensors_list, name="sensors_list"),
    path("sensor/heartbeat",check_sensor_heartbeat, name="sensor_heartbeat"),
    # -------------------------- Sesnors Urls----------------------------#
    path("add-device", add_device, name="add_device"),
    path("devices-list", devices_list, name="devices_list"),
]