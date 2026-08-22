"""License gate for paid extensions.

require_license() is called by an extension's own code before doing gated
work, per docs/extension-architecture.md §5. This is an honest, plain
function — no obfuscation on the gate itself in this module (the design
doc's "compiled + checksum" hardening is a packaging/distribution concern
for extension authors, not something this check needs to hide from
itself). Anyone with server access can delete this call; the actual
enforcement is the daily server-side revalidation
(configurations.extensions.tasks.revalidate_extension_licenses).
"""

from django.utils import timezone

from configurations.models import ExtensionLicense


class LicenseRequiredError(Exception):
    """Raised when an extension has no active, unexpired license for an organization."""


def require_license(extension_name: str, organization) -> None:
    """Raise unless there's an active, unexpired license for this (extension, org) pair.

    Args:
        extension_name: InstalledExtension.name of the licensed extension.
        organization: the Organization to check.

    Raises:
        LicenseRequiredError: if no matching active/unexpired ExtensionLicense exists.
    """
    has_license = ExtensionLicense.objects.filter(
        extension__name=extension_name,
        organization=organization,
        status="active",
        valid_until__gte=timezone.now(),
    ).exists()
    if not has_license:
        raise LicenseRequiredError(
            f"'{extension_name}' has no active license for organization '{organization}'"
        )
