from django.urls import path

from iot.views.iot_device_views import (
    add_device,
    device_details,
    device_pairing_status,
    devices_list,
    edit_device,
    paired_device_and_fetched_sesnors,
    search_devices,
    unpair_device,
)
from iot.views.iot_sensors_views import (
    create_sensor_device,
    edit_sensor,
    get_sensor_historical_data,
    search_sensors,
    sensor_details,
    sensors_list,
)
from iot.views.iot_threshold_views import (
    ack_alarm,
    create_threshold_rule,
    delete_threshold_rule,
    resolve_alarm,
    sensors_by_device,
    threshold_alarm_management,
    update_threshold_rule,
)

app_name = "iot"

urlpatterns = [
    # -------------------------- Sesnors Urls----------------------------#
    path("create-sensor", create_sensor_device, name="add_sensor"),
    path("edit-sensor/<uuid:id>", edit_sensor, name="edit_sensor"),
    path("sensor-details/<uuid:id>", sensor_details, name="sensor_details"),
    path("sensors-list", sensors_list, name="sensors_list"),
    path("sensors-search/<int:page>", search_sensors, name="sensors_search"),
    # -------------------------- Device Urls----------------------------#
    path("add-device", add_device, name="add_device"),
    path("edit-device/<uuid:id>", edit_device, name="edit_device"),
    path("details/<uuid:id>", device_details, name="device_details"),
    path("devices-list", devices_list, name="devices_list"),
    path(
        "devices/<str:device_id>/paired",
        paired_device_and_fetched_sesnors,
        name="pair_device",
    ),
    path(
        "devices/<str:device_id>/pairing-status",
        device_pairing_status,
        name="device_pairing_status",
    ),
    path(
        "devices/<str:device_id>/unpaired",
        unpair_device,
        name="unpair_device",
    ),
    path(
        "sensor/<str:sensor_id>/historical-data",
        get_sensor_historical_data,
        name="sensor_historical_data",
    ),
    path("devices-search/<int:page>", search_devices, name="devices_search"),
    # -------------------------- Thresholds & Alarms Urls----------------------------#
    path("thresholds-alarms/", threshold_alarm_management, name="threshold_alarms"),
    path("thresholds/create/", create_threshold_rule, name="create_threshold"),
    path(
        "thresholds/<int:threshold_id>/update/",
        update_threshold_rule,
        name="update_threshold",
    ),
    path(
        "thresholds/<int:threshold_id>/delete/",
        delete_threshold_rule,
        name="delete_threshold",
    ),
    path("alarms/<int:alarm_id>/ack/", ack_alarm, name="ack_alarm"),
    path("alarms/<int:alarm_id>/resolve/", resolve_alarm, name="resolve_alarm"),
    path(
        "sensors-by-device/<uuid:device_id>/",
        sensors_by_device,
        name="sensors_by_device",
    ),
]
