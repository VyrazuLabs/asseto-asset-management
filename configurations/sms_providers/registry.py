"""
Provider registry — maps provider name strings to their concrete classes.

To add a new provider:
  1. Create  configurations/sms_providers/<name>.py  with a class that
     subclasses SMSProvider.
  2. Import it here and add one line to PROVIDER_REGISTRY.
  Nothing else changes — service.py, views, models all stay untouched.
"""

from __future__ import annotations

from .msg91 import MSG91Provider
from .twilio import TwilioProvider

# Registry of supported providers.
# key   : matches SMSConfiguration.provider field value
# value : concrete SMSProvider subclass
PROVIDER_REGISTRY: dict[str, type] = {
    "msg91": MSG91Provider,
    "twilio": TwilioProvider,
    # "sns": SNSProvider,   ← add future providers here
}


def get_provider_class(name: str) -> type:
    """Return the provider class for the given name, or raise ValueError."""
    cls = PROVIDER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(
            f"SMS provider '{name}' is not registered. "
            f"Available providers: {list(PROVIDER_REGISTRY.keys())}"
        )
    return cls


def get_all_providers_metadata() -> dict[str, dict]:
    """
    Return a dict of provider_key -> credential_fields() for all registered providers.
    Used by the view to build the config form dynamically without hardcoding.
    """
    return {
        key: {"fields": cls.credential_fields()}
        for key, cls in PROVIDER_REGISTRY.items()
    }
