import json

from django.shortcuts import get_object_or_404
import paho.mqtt.client as mqtt

from iot.models.device_models import Device

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)


def on_connect(client, userdata, flags, reason_code, properties):
    print("MQTT connected:", reason_code)

    client.subscribe([
        ("sensor/+/pair", 0),
        ("devices/+/pair", 1),
    ])

    print("Subscribed to heartbeat topics")


def on_message(client, userdata, message):
    parts = message.topic.split("/")

    if len(parts) >= 3:
        device_id = parts[1]

        print(
            f"Message: {message.payload.decode()}, "
            f"device id: {device_id}"
        )

    if message.topic.startswith("devices/") and message.topic.endswith("/pair"):
        payload= json.loads(message.payload.decode())

        device_sn=payload["device_id"]

        device=get_object_or_404(Device, device_sn=device_sn)

        device.is_paired=Device.PairingChoice.PAIRED
        device.save(update_fields=["is_paired"])
        print(f"Device {device_sn} paired")

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    for reason_code in reason_code_list:
        if reason_code.is_failure:
            print(f"Subscription failed: {reason_code}")
        else:
            print(f"Subscription granted QoS: {reason_code.value}")


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_subscribe = on_subscribe


def start_mqtt():
    mqtt_client.connect("localhost", 1883, 60)
    mqtt_client.loop_start()