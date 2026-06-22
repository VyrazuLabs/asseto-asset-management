"""Tests for the shared base factories in ``common.factories``.

Verifies that ``UserFactory`` produces a persisted, valid ``User`` with an
``organization`` assigned and a usable hashed password, exercising the
custom ``UserManager.create_user`` path used by the factory.
"""

import pytest

from common.factories import OrganizationFactory, UserFactory


@pytest.mark.django_db
def test_user_factory_creates_valid_user():
    """UserFactory() should create a persisted user with a valid organization.

    Asserts the user has a primary key (was saved), is linked to an
    ``Organization`` instance, and has a usable hashed password set via
    ``UserManager.create_user``.
    """
    # Act
    user = UserFactory()

    # Assert
    assert user.pk is not None
    assert user.organization is not None
    assert user.organization.pk is not None
    assert user.check_password("TestPass123!")


@pytest.mark.django_db
def test_organization_factory_creates_valid_organization():
    """OrganizationFactory() should create a persisted organization with a name."""
    # Act
    organization = OrganizationFactory()

    # Assert
    assert organization.pk is not None
    assert organization.name
