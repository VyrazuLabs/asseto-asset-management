"""Daily re-validation of extension licenses against the external license server.

Cache-tolerant on network failure — a licensed extension keeps working on
its cached valid_until if the license server is briefly unreachable; only
an explicit invalid/revoked response from the server invalidates
immediately. See docs/extension-architecture.md §5.
"""

from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from configurations.extensions.license_client import validate as license_client_validate
from configurations.models import ExtensionLicense


def revalidate_one_license(license_row: ExtensionLicense, base_url: str, validate_fn=None) -> None:
    """Re-validate a single ExtensionLicense row against the license server.

    Args:
        license_row: the row to revalidate.
        base_url: license server base URL.
        validate_fn: callable(base_url, activation_token) -> dict; defaults
            to the real license_client.validate.

    On success: refreshes status/valid_until/last_checked_at.
    On an explicit "invalid"/"revoked" server response: sets status
    "invalid" immediately.
    On any other exception (network failure, timeout, etc.): leaves
    status/valid_until untouched — cached validity still governs
    require_license() until it actually lapses — and records the error.
    """
    validate_fn = validate_fn or (
        lambda base_url, activation_token: license_client_validate(base_url, activation_token)
    )

    try:
        result = validate_fn(base_url, license_row.activation_token)
    except Exception as exc:
        license_row.last_error = str(exc)
        license_row.save(update_fields=["last_error"])
        return

    server_status = result.get("status")
    license_row.last_checked_at = timezone.now()
    license_row.last_error = None

    if server_status in ("invalid", "revoked"):
        license_row.status = "invalid"
    else:
        license_row.status = "active"
        valid_until = result.get("valid_until")
        if valid_until:
            license_row.valid_until = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))

    license_row.save(update_fields=["status", "valid_until", "last_checked_at", "last_error"])


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3, acks_late=True)
def revalidate_extension_licenses(self):
    """Celery beat task: re-validate every ExtensionLicense row daily."""
    base_url = getattr(settings, "LICENSE_SERVER_URL", None)
    if not base_url:
        return
    for license_row in ExtensionLicense.objects.exclude(status="expired"):
        revalidate_one_license(license_row, base_url)
