from django.urls import path

from iot.views.iot_device_views import add_device, edit_device, device_details, devices_list, search_devices
from iot.views.iot_sensors_views import create_sensor_device, edit_sensor, sensor_details, sensors_list, search_sensors, check_sensor_heartbeat
from iot.views.iot_threshold_views import threshold_alarm_management, create_threshold_rule, update_threshold_rule, delete_threshold_rule, trigger_alarm, ack_alarm, resolve_alarm, sensors_by_device

app_name = "iot"

urlpatterns = [
    # -------------------------- Sesnors Urls----------------------------#
    path("create-sensor", create_sensor_device, name="add_sensor"),
    path("edit-sensor/<uuid:id>", edit_sensor, name="edit_sensor"),
    path("sensor-details/<uuid:id>", sensor_details, name="sensor_details"),
    path("sensors-list", sensors_list, name="sensors_list"),
    path("sensors-search/<int:page>", search_sensors, name="sensors_search"),
    path("sensor/heartbeat",check_sensor_heartbeat, name="sensor_heartbeat"),
    # -------------------------- Sesnors Urls----------------------------#
    path("add-device", add_device, name="add_device"),
    path("edit-device/<uuid:id>", edit_device, name="edit_device"),
    path("details/<uuid:id>", device_details, name="device_details"),
    path("devices-list", devices_list, name="devices_list"),
    path("devices-search/<int:page>", search_devices, name="devices_search"),
    # -------------------------- Thresholds & Alarms Urls----------------------------#
    path("thresholds-alarms/", threshold_alarm_management, name="threshold_alarms"),
    path("thresholds/create/", create_threshold_rule, name="create_threshold"),
    path("thresholds/<int:threshold_id>/update/", update_threshold_rule, name="update_threshold"),
    path("thresholds/<int:threshold_id>/delete/", delete_threshold_rule, name="delete_threshold"),
    path("thresholds/<int:threshold_id>/trigger/", trigger_alarm, name="trigger_alarm"),
    path("alarms/<int:alarm_id>/ack/", ack_alarm, name="ack_alarm"),
    path("alarms/<int:alarm_id>/resolve/", resolve_alarm, name="resolve_alarm"),
    path("sensors-by-device/<uuid:device_id>/", sensors_by_device, name="sensors_by_device"),
]