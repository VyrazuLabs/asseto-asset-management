import threading

from iot.mqtt_client import subscribe_and_listen

SENSOR_TOPIC: list = "device/+/sensor/reading"
DEVICE_HEARTBEAT_TOPIC: str = "device/+/+/heartbeat"


def start_sensor_stream():
    """
    1. sensor-websocket-worker — pushes every reading to connected
       WebSocket clients in real-time via Django Channels.

    2. sensor-db-worker — buffers readings and bulk-inserts them into
       ``SesnorData`` in configurable batches so the DB write path never
       becomes a bottleneck.

    Both workers receive their own queue so every MQTT message is delivered
    to both independently (the MQTT client fans-out to all registered queues).
    """

    from iot.sensor_db_worker import sensor_db_worker
    from iot.websocket_worker import sensor_websocket_worker

    # Queue 1 → WebSocket push
    ws_queue = subscribe_and_listen(SENSOR_TOPIC)

    # Queue 2 → DB persistence (separate subscription = independent queue)
    db_queue = subscribe_and_listen(SENSOR_TOPIC)

    ws_worker = threading.Thread(
        target=sensor_websocket_worker,
        args=(ws_queue,),
        daemon=True,
        name="sensor-websocket-worker",
    )

    db_worker = threading.Thread(
        target=sensor_db_worker,
        args=(db_queue,),
        daemon=True,
        name="sensor-db-worker",
    )

    ws_worker.start()
    db_worker.start()

    print(f"[Sensor Stream] Listening to {SENSOR_TOPIC}")
    print("[Sensor Stream] WebSocket worker started")
    print("[Sensor Stream] DB persistence worker started")


def start_device_heartbeat_stream():
    from iot.device_heartbeat_worker import device_heartbeat_worker

    heartbeat_queue = subscribe_and_listen(DEVICE_HEARTBEAT_TOPIC, include_topic=True)

    heartbeat_worker = threading.Thread(
        target=device_heartbeat_worker,
        args=(heartbeat_queue,),
        daemon=True,
        name="device-heartbeat-worker",
    )

    heartbeat_worker.start()

    print(f"[Device Heartbeat Stream] Listening to {DEVICE_HEARTBEAT_TOPIC}")
    print("[Device Heartbeat Stream] Worker started")
