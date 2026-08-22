"""Tests for configurations.extensions.license.require_license.

The gate a licensed extension calls before doing gated work — checks for
an active, unexpired ExtensionLicense row for that (extension, org) pair.
See docs/extension-architecture.md §5.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from common.factories import OrganizationFactory
from configurations.extensions.license import LicenseRequiredError, require_license
from configurations.models import ExtensionLicense, InstalledExtension


def _installed_extension(name="paid_extension"):
    return InstalledExtension.objects.create(
        name=name,
        app_label=f"ext_{name}",
        version="1.0.0",
        status="active",
        source="local",
        manifest_json={"name": name, "license_required": True},
    )


@pytest.mark.django_db
def test_require_license_raises_when_no_license_row_exists():
    # Arrange
    ext = _installed_extension()
    org = OrganizationFactory()

    # Act / Assert
    with pytest.raises(LicenseRequiredError):
        require_license(ext.name, org)


@pytest.mark.django_db
def test_require_license_raises_when_license_expired():
    # Arrange
    ext = _installed_extension()
    org = OrganizationFactory()
    ExtensionLicense.objects.create(
        extension=ext,
        organization=org,
        activation_token="tok",
        status="active",
        valid_until=timezone.now() - timedelta(days=1),
    )

    # Act / Assert
    with pytest.raises(LicenseRequiredError):
        require_license(ext.name, org)


@pytest.mark.django_db
def test_require_license_raises_when_status_invalid():
    # Arrange
    ext = _installed_extension()
    org = OrganizationFactory()
    ExtensionLicense.objects.create(
        extension=ext,
        organization=org,
        activation_token="tok",
        status="invalid",
        valid_until=timezone.now() + timedelta(days=30),
    )

    # Act / Assert
    with pytest.raises(LicenseRequiredError):
        require_license(ext.name, org)


@pytest.mark.django_db
def test_require_license_passes_when_active_and_unexpired():
    # Arrange
    ext = _installed_extension()
    org = OrganizationFactory()
    ExtensionLicense.objects.create(
        extension=ext,
        organization=org,
        activation_token="tok",
        status="active",
        valid_until=timezone.now() + timedelta(days=30),
    )

    # Act / Assert — should not raise
    require_license(ext.name, org)
