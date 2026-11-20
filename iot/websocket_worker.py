import json
import queue

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from iot.utils.threshold_utils import alarm_engine


def sensor_websocket_worker(message_queue: queue.Queue):
    channel_layer = get_channel_layer()
    print("[WS worker] started")

    while True:
        payload = message_queue.get()

        try:
            data = json.loads(payload)

        except json.JSONDecodeError:
            data = payload

        print(f"[WS Worker] Recieved: {data}")

        from iot.constants import UNIT_BY_TYPE
        from iot.helpers import get_sensor_value

        transformed = {
            "sensors": [
                {
                    "id": sensor["id"],
                    "type": sensor["type"],
                    "value": get_sensor_value(sensor),
                    "unit": UNIT_BY_TYPE.get(sensor.get("type"), ""),
                    "humidity": sensor.get("humidity"),
                }
                for sensor in data.get("sensors", [])
            ]
        }

        # Evaluate each sensor reading against all its thresholds, skipping missing values
        for sensor in transformed["sensors"]:
            try:
                # If the sensor value is None, skip alarm evaluation
                if sensor["value"] is None:
                    print(
                        f"[WS Worker] No value for sensor {sensor['id']}, skipping alarm evaluation"
                    )
                    continue
                alarm_engine.evaluate(sensor["id"], sensor["value"])
            except Exception as exc:
                print(f"[WS Worker] AlarmEngine error for sensor {sensor['id']}: {exc}")

        async_to_sync(channel_layer.group_send)(
            "sensor_data", {"type": "sensor_message", "data": transformed}
        )
