from datetime import datetime, timezone
import json
import logging
import queue
import threading
import time

logger = logging.getLogger(__name__)

BATCH_SIZE: int = 500  # flush early when this many records queue up
FLUSH_INTERVAL: float = 0.3  # seconds between periodic flushes

VALUE_KEYS = ("value", "reading", "reading_value", "measurement")
LEGACY_TYPE_KEYS = ("temperature", "humidity", "sound")


def _extract_value(sensor: dict):
    if not isinstance(sensor, dict):
        return None

    sensor_type = sensor.get("type")
    keys = []
    if isinstance(sensor_type, str) and sensor_type:
        keys.append(sensor_type)
    keys.extend(VALUE_KEYS)
    keys.extend(key for key in LEGACY_TYPE_KEYS if key not in keys)

    for key in keys:
        raw = sensor.get(key)
        if raw is None or isinstance(raw, bool):
            continue
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    return None


def _bulk_insert(batch: list) -> None:
    """Import models here to avoid AppRegistryNotReady at module load time."""

    """Late import, Django ORM must not be touched at module level because
    this module is imported before Django's app registry is ready."""

    from iot.models.sensor_models import SesnorData

    objects = []
    for entry in batch:

        # skip the data if timestamp is missing
        if entry.get("timestamp") is None:
            continue

        # Timestamp from MQTT broker is in milliseconds — convert to seconds
        raw_ts = entry.get("timestamp")
        timestamp = datetime.fromtimestamp(raw_ts / 1000, tz=timezone.utc)

        sensors = entry.get("sensors", [])
        if isinstance(sensors, dict):
            sensors = [sensors]
        if not isinstance(sensors, (list, tuple)):
            continue

        try:
            for sensor in sensors:
                if not isinstance(sensor, dict):
                    continue
                sensor_id = sensor.get("id") or sensor.get("sensor_id")
                value = _extract_value(sensor)
                if sensor_id is None or value is None:
                    continue
                objects.append(
                    SesnorData(sensor_id=str(sensor_id), value=value, timestamp=timestamp)
                )
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("[DB Worker] Skipping malformed record %s — %s", entry, exc)

    if objects:
        try:
            SesnorData.objects.bulk_create(objects, ignore_conflicts=True)
            logger.debug("[DB Worker] Inserted %d records", len(objects))
        except Exception as exc:
            logger.error("[DB Worker] bulk_create failed: %s", exc)


def sensor_db_worker(message_queue: queue.Queue) -> None:
    """
    Long-running thread target.

    Reads JSON payloads from *message_queue*, buffers them, and flushes
    to the DB either when the batch is full or on the periodic timer.

    """

    buffer: list = []
    lock = threading.Lock()
    last_flush = time.monotonic()

    def flush() -> None:
        nonlocal buffer, last_flush
        with lock:
            if not buffer:
                last_flush = time.monotonic()
                return
            batch, buffer = buffer, []
        # DB I/O outside the lock so other threads can keep appending.
        _bulk_insert(batch)
        last_flush = time.monotonic()

    logger.info(
        "[DB Worker] started — batch=%d interval=%.1fs", BATCH_SIZE, FLUSH_INTERVAL
    )

    while True:
        # Block for at most FLUSH_INTERVAL before doing a periodic flush.
        timeout = max(0.0, FLUSH_INTERVAL - (time.monotonic() - last_flush))
        try:
            payload = message_queue.get(timeout=timeout)
        except queue.Empty:
            # Periodic flush... nothing new arrived in time.
            flush()
            continue

        # Parse the incoming payload.
        try:
            data = json.loads(payload) if isinstance(payload, str) else payload
        except json.JSONDecodeError:
            logger.warning("[DB Worker] Non-JSON payload dropped: %s", payload)
            continue

        with lock:
            buffer.append(data)
            should_flush = len(buffer) >= BATCH_SIZE

        if should_flush:
            flush()
