"""
Celery tasks for asynchronous SMS delivery.

Imported lazily by SMSService._dispatch() so that projects without Celery
(or with a down broker) can still fall back to thread-based dispatch.
"""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


class RetryableSMSError(Exception):
    """Raised for transient SMS delivery failures that should be retried by Celery."""


@shared_task(
    bind=True,
    autoretry_for=(RetryableSMSError,),
    retry_backoff=True,          # exponential back-off: 2s, 4s, 8s …
    max_retries=3,
    acks_late=True,              # re-queue if worker dies mid-flight
    name="configurations.sms_tasks.send_sms_task",
)
def send_sms_task(self, *, config_id: str, to: str, message: str,
                  entity_type: str = "", entity_id: str = "", **provider_kwargs):
    """
    Celery task: fetch config and deliver an SMS via the active provider.

    All arguments are JSON-serializable primitives so the task payload is
    broker-safe regardless of serializer settings.

    Transient failures (network/5xx) retry up to 3 times with exponential back-off.
    Permanent failures (bad credentials, 4xx, invalid phone) fail without retrying.
    """
    from configurations.sms_service import SMSService  # noqa: PLC0415 (avoid circular at module level)

    logger.info(
        "Celery SMS task started: config_id=%s to=%s entity=%s/%s",
        config_id, to, entity_type, entity_id,
    )

    is_last_attempt = self.request.retries >= self.max_retries
    result = SMSService._run_sync_from_config_id(
        config_id=config_id,
        to=to,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        write_log_on_retryable_failure=is_last_attempt,
        **provider_kwargs,
    )

    if not result.get("success") and result.get("retryable"):
        error_msg = result.get("error") or result.get("reason") or "Transient SMS send failure"
        raise RetryableSMSError(error_msg)

    return result
