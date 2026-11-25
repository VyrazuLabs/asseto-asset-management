"""Utility helper functions for the iot package."""

DEVICE_ID_KEYS = ("device_id",)
META_KEYS = DEVICE_ID_KEYS + ("timestamp", "sensors")


def build_telemetry_sensor(device_id, key, value):
    """Build one websocket sensor entry from a raw MQTT key/value pair."""
    return {"id": device_id, "type": key, "value": value}


def transform_telemetry_payload(data):
    """Normalize MQTT telemetry into the websocket sensor list shape.

    Payload keys are used exactly as received, for example::

        {"device_id": "machine_001", "timestamp": 1795591800000,
         "temperature": 29.5, "sound_level": 42}

    becomes one sensor per remaining key with ``type`` set to that raw key.
    """
    entries = data if isinstance(data, list) else [data]
    sensors = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        device_id = next((entry[key] for key in DEVICE_ID_KEYS if key in entry), None)

        if device_id is not None:
            for key, value in entry.items():
                if key in META_KEYS or isinstance(value, dict):
                    continue
                sensors.append(build_telemetry_sensor(device_id, key, value))
            continue

        legacy_sensors = entry.get("sensors")
        if isinstance(legacy_sensors, (list, tuple)):
            for sensor in legacy_sensors:
                if not isinstance(sensor, dict):
                    continue
                key = sensor.get("type")
                device = sensor.get("device_id") or sensor.get("id")
                value = sensor.get(key) if key else None
                if value is None:
                    value = sensor.get("value")
                sensors.append(build_telemetry_sensor(device, key, value))
            continue

        if isinstance(legacy_sensors, dict):
            for device, readings in legacy_sensors.items():
                if isinstance(readings, dict):
                    for key, value in readings.items():
                        sensors.append(build_telemetry_sensor(device, key, value))
            continue

        for device, readings in entry.items():
            if isinstance(readings, dict):
                for key, value in readings.items():
                    sensors.append(build_telemetry_sensor(device, key, value))

    return {"sensors": sensors}
