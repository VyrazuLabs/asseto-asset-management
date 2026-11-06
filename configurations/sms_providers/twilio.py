"""
Twilio SMS provider.

API reference: https://www.twilio.com/docs/sms
Global SMS delivery in E.164 format.

Credentials required (stored in SMSConfiguration.credentials JSON):
  account_sid : Twilio Account SID (ACxxxx...)
  auth_token  : Primary Auth Token
  from_number : SMS-capable Twilio number or alphanumeric sender (E.164)
"""

from __future__ import annotations

import logging

import requests

from .base import SMSProvider, SMSResult

logger = logging.getLogger(__name__)


class TwilioProvider(SMSProvider):
    REQUIRED_FIELDS = ["account_sid", "auth_token", "from_number"]

    # ------------------------------------------------------------------
    # UI metadata
    # ------------------------------------------------------------------

    @classmethod
    def credential_fields(cls) -> list[dict]:
        return [
            {
                "key": "account_sid",
                "label": "Account SID",
                "type": "text",
                "placeholder": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "help": "Account SID located on your Twilio Console dashboard.",
                "required": True,
            },
            {
                "key": "auth_token",
                "label": "Auth Token",
                "type": "password",
                "placeholder": "Enter your Twilio Auth Token",
                "help": "Primary Auth Token from your Twilio Console.",
                "required": True,
            },
            {
                "key": "from_number",
                "label": "From Number / Sender ID",
                "type": "text",
                "placeholder": "+1234567890",
                "help": "Active Twilio phone number (E.164 format) or approved alphanumeric sender.",
                "required": True,
            },
        ]

    # ------------------------------------------------------------------
    # Phone normalization
    # ------------------------------------------------------------------

    def sanitize_phone(self, phone: str) -> str:
        """Twilio requires E.164 format: +<country_code><number>."""
        cleaned = "".join(ch for ch in str(phone) if ch.isdigit() or ch == "+")
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned

    # ------------------------------------------------------------------
    # Send
    # ------------------------------------------------------------------

    def send(self, *, to: str, message: str, **kwargs) -> SMSResult:
        account_sid = self.credentials["account_sid"]
        auth_token = self.credentials["auth_token"]
        from_number = self.credentials["from_number"]

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

        try:
            resp = requests.post(
                url,
                data={"From": from_number, "To": to, "Body": message},
                auth=(account_sid, auth_token),
                timeout=10,
            )
            try:
                resp_data = resp.json()
            except Exception:
                resp_data = {"raw": resp.text, "status_code": resp.status_code}

            is_success = resp.status_code in (200, 201) and not resp_data.get("error_code")

            if is_success:
                return SMSResult(
                    success=True,
                    message_id=resp_data.get("sid"),
                    raw_response=resp_data,
                )
            return SMSResult(
                success=False,
                error=resp_data.get("message") or f"Twilio HTTP {resp.status_code}",
                raw_response=resp_data,
            )

        except requests.exceptions.Timeout:
            return SMSResult(success=False, error="Twilio request timed out.", raw_response={})
        except Exception as exc:
            logger.exception("Twilio send failed: %s", exc)
            return SMSResult(success=False, error=str(exc), raw_response={})
