"""
Central SMS dispatching service for Asseto.

Design
------
- Provider-agnostic: SMSService never imports or references a concrete provider.
  All provider logic lives in configurations/sms_providers/.
- Dispatch strategy (best-effort, never crashes callers):
    1. Try Celery async  (send_sms_task.delay) — preferred; non-blocking.
    2. If Celery is unavailable / broker down → fallback to a daemon thread
       (non-blocking, keeps the HTTP response fast).
    3. If thread dispatch itself errors → last-resort synchronous send.
  The sync path (_send_sync) is also the shared implementation used by all
  three branches; it's the single place that calls the provider and writes
  the SMSLog row.

Adding a new SMS provider: add a file in sms_providers/ and one line in
sms_providers/registry.py. This file never needs to change.
"""

from __future__ import annotations

import logging
import threading

from django.db import OperationalError

from configurations.models import Extensions, SMSConfiguration, SMSLog
from configurations.sms_providers.registry import get_provider_class

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Celery task import — optional; gracefully degraded when broker is offline
# ---------------------------------------------------------------------------

def _get_sms_task():
    """Return the Celery send_sms_task, or None if Celery is not available."""
    try:
        from configurations.sms_tasks import send_sms_task  # noqa: PLC0415
        return send_sms_task
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SMSService:
    """Provider-agnostic SMS dispatcher.

    Public API (call from signals / views):
        SMSService.send(organization=org, to=phone, message=msg, ...)
        SMSService.notify_client_ticket_created(ticket)

    Both methods are non-blocking — they always return quickly.
    """

    # ------------------------------------------------------------------
    # Guards
    # ------------------------------------------------------------------

    @staticmethod
    def is_active(organization) -> bool:
        """True when SMS extension is enabled AND an active provider is configured."""
        if not organization:
            return False
        try:
            ext_active = Extensions.objects.filter(
                organization=organization,
                entity_name="SMS",
                status=1,
            ).exists()
            if not ext_active:
                return False
            return SMSConfiguration.objects.filter(
                organization=organization, is_active=True
            ).exists()
        except OperationalError:
            return False

    @staticmethod
    def get_active_config(organization):
        """Return the active SMSConfiguration for the org, or None."""
        if not SMSService.is_active(organization):
            return None
        return SMSConfiguration.objects.filter(
            organization=organization, is_active=True
        ).first()

    # ------------------------------------------------------------------
    # Public dispatch entry point
    # ------------------------------------------------------------------

    @classmethod
    def send(
        cls,
        *,
        organization,
        to: str,
        message: str,
        entity_type: str = "",
        entity_id: str = "",
        **provider_kwargs,
    ) -> None:
        """
        Non-blocking SMS dispatch.

        Tries Celery first; falls back to a daemon thread; last resort: sync.
        Never raises — all failures are logged.

        provider_kwargs: passed through to the provider's send() (e.g. ticket_id,
        subject, extra_vars, org_name). Unknown kwargs are ignored by providers.
        """
        if not organization:
            logger.debug("SMS skipped: no organization provided.")
            return

        config = cls.get_active_config(organization)
        if not config:
            logger.debug("SMS skipped: extension inactive or no active config for %s.", organization)
            return

        to = to.strip() if to else ""
        if not to:
            logger.warning("SMS skipped: empty recipient phone.")
            return

        # Serialize only what Celery needs (primitive types, no ORM objects)
        dispatch_kwargs = dict(
            config_id=str(config.id),
            to=to,
            message=message,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else "",
            **{k: v for k, v in provider_kwargs.items() if isinstance(v, (str, int, float, bool, dict, list, type(None)))},
        )

        cls._dispatch(config, dispatch_kwargs)

    @classmethod
    def _dispatch(cls, config, dispatch_kwargs: dict) -> None:
        """Try Celery → thread → sync, in that order."""
        # 1. Celery async (preferred)
        task = _get_sms_task()
        if task is not None:
            try:
                task.delay(**dispatch_kwargs)
                logger.debug("SMS queued via Celery for config %s.", config.id)
                return
            except Exception as exc:
                logger.warning(
                    "Celery broker unavailable (%s); falling back to thread dispatch.", exc
                )

        # 2. Daemon thread fallback (non-blocking, no broker dependency)
        try:
            thread = threading.Thread(
                target=cls._run_sync_from_config_id,
                kwargs=dispatch_kwargs,
                daemon=True,
                name="sms-send",
            )
            thread.start()
            logger.debug("SMS dispatched via daemon thread for config %s.", config.id)
            return
        except Exception as exc:
            logger.warning("Thread dispatch failed (%s); sending synchronously.", exc)

        # 3. Last-resort synchronous send (blocks, but guarantees delivery attempt)
        try:
            cls._run_sync_from_config_id(**dispatch_kwargs)
        except Exception as exc:
            logger.exception("Synchronous SMS fallback also failed: %s", exc)

    # ------------------------------------------------------------------
    # Sync implementation — shared by Celery task AND thread fallback
    # ------------------------------------------------------------------

    @classmethod
    def _run_sync_from_config_id(
        cls,
        *,
        config_id: str,
        to: str,
        message: str,
        entity_type: str = "",
        entity_id: str = "",
        **provider_kwargs,
    ) -> dict:
        """
        Fetch the config by ID and delegate to _send_sync.
        Called from the Celery task and from the thread fallback.
        Returns a result dict for Celery result backend (optional).
        """
        try:
            config = SMSConfiguration.objects.get(id=config_id)
        except SMSConfiguration.DoesNotExist:
            logger.error("SMSConfiguration %s not found; SMS aborted.", config_id)
            return {"success": False, "reason": "Config not found."}

        return cls._send_sync(
            config=config,
            to=to,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            **provider_kwargs,
        )

    @classmethod
    def _send_sync(
        cls,
        *,
        config: SMSConfiguration,
        to: str,
        message: str,
        entity_type: str = "",
        entity_id: str = "",
        **provider_kwargs,
    ) -> dict:
        """
        Synchronous send: instantiate provider → sanitize phone → send → log.

        This is the ONLY place that knows the SMSProvider interface.
        It never inspects config.provider by name — it asks the registry.
        """
        try:
            ProviderClass = get_provider_class(config.provider)
            provider = ProviderClass(config.credentials)
        except ValueError as exc:
            logger.error("Provider error for config %s: %s", config.id, exc)
            return {"success": False, "reason": str(exc)}

        cleaned_phone = provider.sanitize_phone(to)
        if not cleaned_phone:
            logger.warning("SMS aborted: phone '%s' could not be sanitized.", to)
            return {"success": False, "reason": "Invalid phone after sanitization."}

        # Pass through any extra kwargs the provider's send() understands
        result = provider.send(to=cleaned_phone, message=message, **provider_kwargs)

        # Write audit log
        try:
            SMSLog.objects.create(
                organization=config.organization,
                provider=config.provider,
                recipient=cleaned_phone,
                message=message,
                status="sent" if result.success else "failed",
                provider_response=result.raw_response or {},
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id else "",
            )
        except Exception as log_exc:
            logger.error("Failed to write SMSLog: %s", log_exc)

        logger.info(
            "SMS via %s to %s: %s",
            config.provider,
            cleaned_phone,
            "sent" if result.success else f"failed — {result.error}",
        )
        return {"success": result.success, "message_id": result.message_id, "error": result.error}

    # ------------------------------------------------------------------
    # High-level helpers (called from signals)
    # ------------------------------------------------------------------

    @classmethod
    def notify_client_ticket_created(cls, ticket) -> bool:
        """
        Send a ticket-creation SMS to the client's first phone contact.

        Returns True if dispatch was attempted, False if skipped.
        Never raises.
        """
        try:
            client = getattr(ticket, "client", None)
            if client is None:
                asset = getattr(ticket, "asset", None)
                client = getattr(asset, "client", None)
            if not client:
                logger.debug("Ticket %s has no linked client; SMS skipped.", ticket.ticket_id)
                return False

            phone = next(
                (
                    getattr(c, "phone", None)
                    for c in client.contacts.all()
                    if getattr(c, "phone", None)
                ),
                None,
            )
            if not phone:
                logger.debug("Client %s has no phone; SMS skipped.", getattr(client, "name", client))
                return False

            org = getattr(ticket, "organization", None)
            if not org or not cls.is_active(org):
                logger.debug("SMS disabled or no org for ticket %s; skipped.", ticket.ticket_id)
                return False

            ticket_id = ticket.ticket_id or "Ticket"
            subject = ticket.subject or "Support Request"
            happy_code = ticket.happy_code or ""
            client_name = getattr(client, "name", None) or "Customer"
            org_name = getattr(org, "name", "Asseto")

            message = (
                f"Asseto: Your support ticket {ticket_id} ({subject}) has been created. "
                f"Happy Code: {happy_code}. "
                f"Please share this happy code with our team when your issue is resolved."
            )

            cls.send(
                organization=org,
                to=phone,
                message=message,
                entity_type="ticket",
                entity_id=str(ticket.id),
                # Provider-level extras
                ticket_id=ticket_id,
                subject=subject,
                org_name=org_name,
                extra_vars={
                    "client_name": client_name,
                    "happy_code": happy_code,
                    "event": "New Ticket Created",
                    "status": "Open",
                },
            )
            return True

        except Exception as exc:
            logger.exception("notify_client_ticket_created failed: %s", exc)
            return False
