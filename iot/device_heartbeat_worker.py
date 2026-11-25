import json
import logging
import queue

from iot.models.device_models import Device
from iot.utils.device_pairing_cache import (
    is_device_paired_and_verified,
    mark_device_paired,
)

logger = logging.getLogger(__name__)


def parse_device_heartbeat(message):
    if isinstance(message, tuple) and len(message) == 2:
        topic, payload = message
    else:
        topic, payload = "", message

    parts = topic.split("/")
    device_type = parts[1] if len(parts) > 1 else None
    device_id = parts[2] if len(parts) > 2 else None

    try:
        data = json.loads(payload) if isinstance(payload, str) else payload
    except json.JSONDecodeError:
        data = {"raw": payload}

    return device_type, device_id, data


def complete_device_pairing(device_id) -> bool:
    updated = Device.undeleted_objects.filter(
        id=device_id,
        is_paired=Device.PairingChoice.PAIRING,
    ).update(is_paired=Device.PairingChoice.PAIRED)
    if updated:
        mark_device_paired(device_id)
    return bool(updated)


def process_device_heartbeat(message) -> bool:
    device_type, device_id, data = parse_device_heartbeat(message)

    if not is_device_paired_and_verified(device_id):
        logger.info(
            "[Device Heartbeat Worker] Ignoring unverified device %s", device_id
        )
        return False

    complete_device_pairing(device_id)
    logger.info(
        "[Device Heartbeat Worker] type=%s device_id=%s data=%s",
        device_type,
        device_id,
        data,
    )
    return True


def device_heartbeat_worker(message_queue: queue.Queue) -> None:
    logger.info("[Device Heartbeat Worker] started")

    while True:
        process_device_heartbeat(message_queue.get())
