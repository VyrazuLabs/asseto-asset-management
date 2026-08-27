import paho.mqtt.client as mqtt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404

from iot.constants import UNIT_MAPPER
from iot.forms.sensor_forms import SensorForm
from iot.models.sensor_models import Sensor
from iot.utils.sensors_utils import create_sensor_list, generate_mqtt_topic, get_sensor_details


@login_required()
def create_sensor_device(request):
    organization = getattr(request.user, "organization", None)
    if request.method == "POST":
        sensor_form = SensorForm(request.POST, organization=organization)

        if sensor_form.is_valid():
            sensor = sensor_form.save(commit=False)
            sensor.organization = organization
            if not sensor.mqtt_topic:
                sensor.mqtt_topic = generate_mqtt_topic(
                    getattr(organization, "id", organization),
                    sensor.sensor_type,
                )
            sensor.save()

            messages.success(request, "Sensor added successfully")
            return redirect("iot:sensors_list")
    else:
        sensor_form = SensorForm(organization=organization)

    return render(
        request,
        "sensors/add-sensor.html",
        {
            "title": "Add sensor",
            "sensor_form": sensor_form,
            "unit_mapper": UNIT_MAPPER,
            "sidebar": "iot",
            "submenu": "sensors",
        },
    )


@login_required()
def edit_sensor(request, id):
    sensor = get_object_or_404(
        Sensor.undeleted_objects, pk=id, organization=request.user.organization
    )
    organization = getattr(request.user, "organization", None)

    if request.method == "POST":
        sensor_form = SensorForm(request.POST, instance=sensor, organization=organization)

        if sensor_form.is_valid():
            sensor_form.save()

            messages.success(request, "Sensor updated successfully")
            return redirect("iot:sensors_list")
    else:
        sensor_form = SensorForm(instance=sensor, organization=organization)

    return render(
        request,
        "sensors/edit-sensor.html",
        {
            "title": f"Edit - {sensor.name}",
            "sensor": sensor,
            "sensor_form": sensor_form,
            "unit_mapper": UNIT_MAPPER,
            "sidebar": "iot",
            "submenu": "sensors",
        },
    )


@login_required()
def sensor_details(request, id):
    context = get_sensor_details(request, id)
    return render(request, "sensors/sensor-detail.html", context)


@login_required()
def sensors_list(request):
    try:
        query_objects = Sensor.undeleted_objects.values(
            "id",
            "name",
            "device__name",
            "sensor_type",
            "unit",
            "is_paired",
            "created_at",
        ).order_by("-created_at")
        if hasattr(request.user, "organization") and request.user.organization:
            query_objects = query_objects.filter(organization=request.user.organization)
        context = create_sensor_list(request, query_objects)
        context["title"] = "Sensors list"
        context["sidebar"] = "iot"
        context["submenu"] = "sensors"
        return render(request, "sensors/sensors-list.html", context=context)
    except Exception as e:
        print(str(e))
        return render(request, "sensors/sensors-list.html", context={"page_object": []})


@login_required()
def search_sensors(request, page):
    try:
        query_objects = Sensor.undeleted_objects.values(
            "id",
            "name",
            "device__name",
            "sensor_type",
            "unit",
            "is_paired",
            "created_at",
        ).order_by("-created_at")
        if hasattr(request.user, "organization") and request.user.organization:
            query_objects = query_objects.filter(organization=request.user.organization)
        context = create_sensor_list(request, query_objects)
    except Exception:
        return HttpResponse(status=500)
    return render(request, "sensors/sensors-data.html", context)


@login_required()
def check_sensor_heartbeat(request):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        # VERSION2 on_connect requires 5 params: client, userdata, flags, reason_code, properties
        def on_connect(client, userdata, flags, reason_code, properties):
            print("Connect with result code", str(reason_code))

            client.subscribe([("sensor/+/heartbeat", 0), ("devices/+/heartbeat", 1)])
            print("Subscribed to sensor/+/heartbeat and devices/+/heartbeat")

        def on_message(client, userdata, message):
            parts = message.topic.split("/")
            device_id = parts[1]

            print(f"Message: {message.payload.decode()}, device id: {device_id}")

        def on_subscribe(client, userdata, mid, reason_code_list, properties):
            # Since we subscribed only for a single channel, reason_code_list contains
            # a single entry
            if reason_code_list[0].is_failure:
                print(f"Broker rejected you subscription: {reason_code_list[0]}")
            else:
                print(f"Broker granted the following QoS: {reason_code_list[0].value}")

        client.on_connect = on_connect
        client.on_message = on_message
        client.on_subscribe = on_subscribe
        client.connect("localhost", 1883, 60)
        # Start the network loop in a background thread so MQTT events
        # (including CONNACK → on_connect) are actually processed.
        client.loop_start()
    except Exception as e:
        print(str(e))

    finally:
        client.disconnect()
    return HttpResponse("Done")
