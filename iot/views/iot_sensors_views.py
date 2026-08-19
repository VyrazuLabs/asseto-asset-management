import paho.mqtt.client as mqtt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from iot.constants import UNIT_MAPPER
from iot.forms.sensor_forms import SensorForm, SensorThresholdForm
from iot.models.sensor_models import Sensor
from iot.utils.sensors_utils import create_sensor_list, generate_mqtt_topic


@login_required()
def create_sensor_device(request):
    organization = getattr(request.user, "organization", None)
    if request.method == "POST":
        sensor_form = SensorForm(request.POST, organization=organization)
        sensor_threshold_form = SensorThresholdForm(request.POST)

        if sensor_form.is_valid() and sensor_threshold_form.is_valid():
            sensor = sensor_form.save(commit=False)
            sensor.organization = organization
            if not sensor.mqtt_topic:
                sensor.mqtt_topic = generate_mqtt_topic(
                    getattr(organization, "id", organization),
                    sensor.sensor_type,
                )
            sensor.save()

            threshold = sensor_threshold_form.save(commit=False)
            threshold.sensor = sensor
            threshold.save()

            messages.success(request, "Sensor added successfully")
            return redirect("iot:sensors_list")
    else:
        sensor_form = SensorForm(organization=organization)
        sensor_threshold_form = SensorThresholdForm()

    return render(
        request,
        "sensors/add-sensor.html",
        {
            "title": "Add sensor",
            "sensor_form": sensor_form,
            "sensor_threshold_form": sensor_threshold_form,
            "unit_mapper": UNIT_MAPPER,
            "sidebar": "iot",
            "submenu": "sensors",
        },
    )


@login_required()
def sensors_list(request):
    try:
        query_objects = Sensor.undeleted_objects.values(
            "id",
            "name",
            "sensor_type",
            "device__asset__name",
            "status",
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
