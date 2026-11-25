import logging

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

DEVICE_PAIRING_HASH = "iot:devices:pairing"
UNPAIRED = "unpaired"
PAIRING = "pairing"
PAIRED = "paired"
VERIFIED = "verified"
PAIRING_STATES = {PAIRING, PAIRED, VERIFIED}

_client = None


def _get_redis_client():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0"),
            decode_responses=True,
            socket_connect_timeout=1,
        )
    return _client


def mark_device_pairing(device_id):
    if not device_id:
        return False
    try:
        _get_redis_client().hset(DEVICE_PAIRING_HASH, device_id, PAIRING)
    except redis.RedisError as exc:
        logger.warning("[Pairing Cache] Could not mark %s: %s", device_id, exc)
        return False
    return True


def mark_device_paired(device_id):
    if not device_id:
        return False
    try:
        _get_redis_client().hset(DEVICE_PAIRING_HASH, device_id, PAIRED)
    except redis.RedisError as exc:
        logger.warning("[Pairing Cache] Could not complete %s: %s", device_id, exc)
        return False
    return True


def mark_device_unpaired(device_id):
    if not device_id:
        return False
    try:
        _get_redis_client().hset(DEVICE_PAIRING_HASH, device_id, UNPAIRED)
    except redis.RedisError as exc:
        logger.warning("[Pairing Cache] Could not unpair %s: %s", device_id, exc)
        return False
    return True


def is_device_paired_and_verified(device_id):
    if not device_id:
        return False
    try:
        state = _get_redis_client().hget(DEVICE_PAIRING_HASH, device_id)
    except redis.RedisError as exc:
        logger.warning("[Pairing Cache] Could not read %s: %s", device_id, exc)
        return False
    return state in PAIRING_STATES
