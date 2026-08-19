# mock_publisher.py
import paho.mqtt.client as mqtt
import time
import random
import json

BROKER_HOST = "localhost"  # or your docker host / service name
BROKER_PORT = 1883

SENSORS = ["sensor1", "sensor2", "sensor3"]
DEVICE = ["device1", "device2", "device3"]

client = mqtt.Client()
client.connect(BROKER_HOST, BROKER_PORT, 60)

print("Publishing mock heartbeats")

try:
    while True:
        for sensors_id in SENSORS:
            # simulate occasional dropout — sensor2 randomly skips
            if sensors_id == "sensor2" and random.random() < 0.3:
                continue

            payload = json.dumps(
                {
                    "type": "sensor",
                    "status": "alive",
                    "battery": random.randint(50, 100),
                }
            )
            client.publish(f"sensor/{sensors_id}/heartbeat", payload)
            print(f"Published heartbeat for {sensors_id}")

        time.sleep(2)

        for device_id in DEVICE:
            # simulate occasional dropout — sensor2 randomly skips
            if device_id == "device3" and random.random() < 0.6:
                continue
            client.publish(
                f"devices/{device_id}/heartbeat",
                json.dumps(
                    {
                        "type": "device",
                        "status": "active",
                        "temp": f"{random.randint(0,40)}C",
                    }
                ),
            )
            print(f"Published heartbeat for {device_id}")

        time.sleep(4)

except KeyboardInterrupt:
    client.disconnect()
