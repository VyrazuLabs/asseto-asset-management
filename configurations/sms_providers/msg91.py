"""
MSG91 SMS provider.

API reference: https://docs.msg91.com/flow
DLT-compliant flow-based SMS for India (TRAI).

Credentials required (stored in SMSConfiguration.credentials JSON):
  auth_key     : MSG91 Auth Key from Settings > Authkey
  template_id  : Flow/Template ID from SMS > Campaign / Flow Builder
  sender_id    : 6-char DLT-approved sender header (optional)
  var_ticket_id: variable key name for ticket id in template (optional, default "ticket_id")
  var_subject  : variable key name for subject in template (optional, default "subject")
"""

from __future__ import annotations

import logging

import requests

from .base import SMSProvider, SMSResult

logger = logging.getLogger(__name__)

_FLOW_URL = "https://control.msg91.com/api/v5/flow/"
_VALIDATE_URL = "https://control.msg91.com/api/v5/report/sms/logs"


class MSG91Provider(SMSProvider):
    REQUIRED_FIELDS = ["auth_key", "template_id"]

    # ------------------------------------------------------------------
    # UI metadata
    # ------------------------------------------------------------------

    @classmethod
    def credential_fields(cls) -> list[dict]:
        return [
            {
                "key": "auth_key",
                "label": "Auth Key",
                "type": "password",
                "placeholder": "Enter your MSG91 Auth Key (e.g. 412356Axxxxxxxx)",
                "help": "Find this in your MSG91 dashboard under Settings > Authkey.",
                "required": True,
            },
            {
                "key": "template_id",
                "label": "Flow ID / Template ID",
                "type": "text",
                "placeholder": "e.g. 64a8b1c4d92...",
                "help": "Flow ID created in MSG91 SMS > Campaign / Flow builder.",
                "required": True,
            },
            {
                "key": "sender_id",
                "label": "Sender ID / Header",
                "type": "text",
                "placeholder": "e.g. ASSETO",
                "help": "6-character DLT-approved sender header (optional).",
                "required": False,
                "maxlength": 6,
            },
            {
                "key": "var_ticket_id",
                "label": "Ticket ID Variable Name (Optional)",
                "type": "text",
                "placeholder": "ticket_id",
                "help": "Key name in your MSG91 template for ticket number (e.g. ticket_id, var1).",
                "required": False,
            },
            {
                "key": "var_subject",
                "label": "Subject Variable Name (Optional)",
                "type": "text",
                "placeholder": "subject",
                "help": "Key name in your MSG91 template for description (e.g. subject, var2).",
                "required": False,
            },
        ]

    # ------------------------------------------------------------------
    # Phone normalization
    # ------------------------------------------------------------------

    def sanitize_phone(self, phone: str) -> str:
        """MSG91 expects digits only with country code, no leading +.
        E.g. '9876543210' -> '919876543210'.
        """
        cleaned = "".join(ch for ch in str(phone) if ch.isdigit() or ch == "+")
        cleaned = cleaned.lstrip("+")
        if len(cleaned) == 10 and not cleaned.startswith("91"):
            cleaned = "91" + cleaned
        return cleaned

    # ------------------------------------------------------------------
    # Send
    # ------------------------------------------------------------------

    def send(
        self,
        *,
        to: str,
        message: str,
        extra_vars: dict | None = None,
        ticket_id: str = "TK-ALERT",
        subject: str | None = None,
        org_name: str = "Asseto",
    ) -> SMSResult:
        """Send via MSG91 Flow API.

        extra_vars can carry additional template variable overrides.
        """
        auth_key = self.credentials["auth_key"]
        template_id = self.credentials["template_id"]
        sender_id = self.credentials.get("sender_id", "")
        var_ticket = self.credentials.get("var_ticket_id") or "ticket_id"
        var_subj = self.credentials.get("var_subject") or "subject"

        extras = extra_vars or {}
        t_subj = (subject or message)[:60]
        t_status = extras.get("status", "Active")
        t_prio = extras.get("priority", "Normal")
        t_event = extras.get("event", "Notification")
        t_name = extras.get("client_name") or extras.get("technician_name", "User")

        recipient_map: dict = {
            "mobiles": to,
            var_ticket: ticket_id,
            var_subj: t_subj,
            # Standard named placeholders
            "ticket_id": ticket_id,
            "subject": t_subj,
            "status": t_status,
            "priority": t_prio,
            "event": t_event,
            "name": t_name,
            "company": org_name,
            # Sequential numeric fallbacks
            "var1": ticket_id,
            "var2": t_subj,
            "var3": t_status,
            "var4": t_prio,
            "var5": t_name,
        }
        for k, v in extras.items():
            if k not in recipient_map:
                recipient_map[k] = str(v)[:60]

        payload: dict = {
            "template_id": template_id,
            "short_url": "0",
            "recipients": [recipient_map],
        }
        if sender_id:
            payload["sender"] = sender_id

        headers = {
            "authkey": auth_key,
            "content-type": "application/json",
            "accept": "application/json",
        }

        try:
            resp = requests.post(_FLOW_URL, json=payload, headers=headers, timeout=10)
            try:
                resp_data = resp.json()
            except Exception:
                resp_data = {"raw": resp.text, "status_code": resp.status_code}

            response_type = resp_data.get("type", "")
            message_id = str(resp_data.get("message", "")).strip() or None
            is_success = (
                resp.status_code in (200, 201, 202)
                and response_type == "success"
                and message_id is not None
            )

            if is_success:
                return SMSResult(success=True, message_id=message_id, raw_response=resp_data)
            return SMSResult(
                success=False,
                error=resp_data.get("message") or f"MSG91 HTTP {resp.status_code}",
                raw_response=resp_data,
            )

        except requests.exceptions.Timeout:
            return SMSResult(success=False, error="MSG91 request timed out.", raw_response={})
        except Exception as exc:
            logger.exception("MSG91 send failed: %s", exc)
            return SMSResult(success=False, error=str(exc), raw_response={})

    def validate_credentials(self) -> tuple[bool, str]:
        """Pre-flight auth check using the report endpoint.

        Returns (is_valid, error_message).
        MSG91's Flow API queues async and always returns success, so we use
        the report endpoint which immediately returns 401 on bad auth keys.
        """
        try:
            resp = requests.get(
                _VALIDATE_URL,
                headers={"authkey": self.credentials["auth_key"], "accept": "application/json"},
                timeout=8,
            )
            data = resp.json() if resp.content else {}
        except Exception:
            # Network error — treat credentials as unverifiable, not invalid
            return True, ""

        if resp.status_code in (401, 403):
            err = (
                str(data.get("errors") or data.get("message") or data.get("msg") or "")
                or "Unauthorized — invalid Auth Key"
            )
            return False, err

        err_text = str(
            data.get("errors") or data.get("message") or data.get("msg") or ""
        ).lower()
        if "authentication failed" in err_text or "invalid authkey" in err_text:
            return False, err_text

        return True, ""
