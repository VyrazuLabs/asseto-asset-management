"""
Base abstractions for the SMS provider layer.

Every concrete SMS provider must subclass SMSProvider and implement:
  - REQUIRED_FIELDS  : list of credential dict keys the provider needs
  - send()           : deliver a single SMS, return SMSResult
  - credential_fields(): return UI field metadata for the config form
  - sanitize_phone() : normalize phone number for the provider's API format

The service layer (sms_service.py) ONLY speaks to this interface — it never
imports or references a concrete provider class directly.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SMSResult:
    """Uniform result object returned by every provider's send() method."""

    success: bool
    message_id: str | None = None
    error: str | None = None
    raw_response: dict = field(default_factory=dict)


class SMSProvider(ABC):
    """
    Abstract base class every SMS provider must implement.

    Lifecycle
    ---------
    1. SMSService fetches the active SMSConfiguration for the org.
    2. It calls get_provider_class(config.provider) → concrete class.
    3. It instantiates:  provider = ConcreteProvider(config.credentials)
       __init__ calls _validate() which raises ValueError for missing keys.
    4. It calls:         result = provider.send(to=phone, message=msg)
    5. It logs SMSLog from result.

    """

    # Subclasses declare which keys must be present in the credentials dict.
    REQUIRED_FIELDS: list[str] = []

    def __init__(self, credentials: dict) -> None:
        self._validate(credentials)
        self.credentials: dict = dict(credentials)

    # ------------------------------------------------------------------
    # Concrete helpers (shared across all providers)
    # ------------------------------------------------------------------

    def _validate(self, credentials: dict) -> None:
        """Raise ValueError if any REQUIRED_FIELDS key is missing."""
        missing = [f for f in self.REQUIRED_FIELDS if not credentials.get(f)]
        if missing:
            raise ValueError(
                f"{self.__class__.__name__} is missing required credentials: {missing}"
            )

    # ------------------------------------------------------------------
    # Abstract interface — every provider MUST implement these
    # ------------------------------------------------------------------

    @abstractmethod
    def send(self, *, to: str, message: str) -> SMSResult:
        """
        Deliver a single SMS.

        Parameters
        ----------
        to      : phone number already normalized by sanitize_phone()
        message : plain-text body (may be ignored by DLT-flow providers)

        Returns SMSResult — never raises; catch exceptions internally.
        """
        ...

    @abstractmethod
    def sanitize_phone(self, phone: str) -> str:
        """
        Normalize a raw phone string to the format expected by this provider's API.

        E.g. MSG91 wants '919876543210'; Twilio wants '+919876543210'.
        """
        ...

    @classmethod
    @abstractmethod
    def credential_fields(cls) -> list[dict]:
        """ 
        Return UI field metadata so the config form can be rendered dynamically.

        Each dict has at minimum:
          key      : str   — matches the key in SMSConfiguration.credentials
          label    : str   — human label shown in the form
          type     : str   — "text" | "password" | "number"
          required : bool
        Optional keys: placeholder, help, maxlength
        """
        ...
