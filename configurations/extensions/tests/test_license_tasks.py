"""Tests for configurations.extensions.tasks.revalidate_one_license.

Daily Celery beat re-validation logic, per docs/extension-architecture.md
§5: success refreshes valid_until/last_checked_at; an explicit
invalid/revoked response from the server invalidates immediately; a
network failure leaves status/valid_until untouched (cache-tolerant — a
brief license-server outage must not lock out already-activated orgs).
validate_fn is injected so no real network call happens in tests.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from common.factories import OrganizationFactory
from configurations.extensions.tasks import revalidate_one_license
from configurations.models import ExtensionLicense, InstalledExtension


def _license_row(status="active", valid_until=None):
    ext = InstalledExtension.objects.create(
        name="paid_extension",
        app_label="ext_paid_extension",
        version="1.0.0",
        status="active",
        source="local",
        manifest_json={"name": "paid_extension", "license_required": True},
    )
    return ExtensionLicense.objects.create(
        extension=ext,
        organization=OrganizationFactory(),
        activation_token="tok-123",
        status=status,
        valid_until=valid_until or (timezone.now() + timedelta(days=1)),
    )


@pytest.mark.django_db
def test_revalidate_refreshes_valid_until_on_success():
    # Arrange
    row = _license_row()
    new_valid_until = timezone.now() + timedelta(days=30)

    def fake_validate(base_url, activation_token):
        return {"status": "active", "valid_until": new_valid_until.isoformat()}

    # Act
    revalidate_one_license(row, base_url="https://license.example.com", validate_fn=fake_validate)

    # Assert
    row.refresh_from_db()
    assert row.status == "active"
    assert row.last_checked_at is not None
    assert row.valid_until.date() == new_valid_until.date()


@pytest.mark.django_db
def test_revalidate_invalidates_immediately_on_explicit_revoke():
    # Arrange
    row = _license_row()

    def fake_validate(base_url, activation_token):
        return {"status": "revoked"}

    # Act
    revalidate_one_license(row, base_url="https://license.example.com", validate_fn=fake_validate)

    # Assert
    row.refresh_from_db()
    assert row.status == "invalid"


@pytest.mark.django_db
def test_revalidate_leaves_status_untouched_on_network_failure():
    # Arrange — cached valid_until is still in the future
    future = timezone.now() + timedelta(days=1)
    row = _license_row(status="active", valid_until=future)

    def failing_validate(base_url, activation_token):
        raise ConnectionError("license server unreachable")

    # Act
    revalidate_one_license(row, base_url="https://license.example.com", validate_fn=failing_validate)

    # Assert — status/valid_until untouched, error recorded
    row.refresh_from_db()
    assert row.status == "active"
    assert row.valid_until.date() == future.date()
    assert "unreachable" in row.last_error
