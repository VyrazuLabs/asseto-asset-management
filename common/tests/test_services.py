"""Tests for the shared service-layer helpers in ``common.services``.

Covers ``BaseMultiTenantService.base_queryset`` (org-scoping, cross-tenant
isolation, soft-delete exclusion) and ``build_asset_conditions_map``
(condition aggregation, including the empty-queryset and multi-condition
branches).
"""

import factory
import factory.django
import pytest

from clients.models import Client
from common.factories import OrganizationFactory
from common.services import BaseMultiTenantService, build_asset_conditions_map


class _ClientFactory(factory.django.DjangoModelFactory):
    """Minimal local factory for ``clients.models.Client``, used only to exercise
    ``BaseMultiTenantService.base_queryset`` against a real org-scoped, soft-delete
    model. No standalone ``clients`` factory module exists yet (out of scope for
    this Phase 0 task); a future phase touching ``clients`` should promote this to
    ``clients/tests/factories.py`` rather than duplicating it.
    """

    class Meta:
        model = Client

    name = factory.Sequence(lambda n: f"Client {n}")
    organization = factory.SubFactory(OrganizationFactory)


@pytest.mark.django_db
def test_base_queryset_returns_only_rows_for_the_given_organization():
    """base_queryset should exclude rows belonging to a different organization."""
    # Arrange
    org_a = OrganizationFactory()
    org_b = OrganizationFactory()
    client_a = _ClientFactory(organization=org_a)
    _ClientFactory(organization=org_b)

    # Act
    result = BaseMultiTenantService.base_queryset(Client, _StubUser(org_a))

    # Assert
    assert list(result) == [client_a]


@pytest.mark.django_db
def test_base_queryset_excludes_soft_deleted_rows():
    """base_queryset should exclude rows where is_deleted=True."""
    # Arrange
    org = OrganizationFactory()
    active_client = _ClientFactory(organization=org)
    deleted_client = _ClientFactory(organization=org)
    deleted_client.soft_delete()

    # Act
    result = BaseMultiTenantService.base_queryset(Client, _StubUser(org))

    # Assert
    assert list(result) == [active_client]


@pytest.mark.django_db
def test_base_queryset_returns_empty_when_organization_has_no_rows():
    """base_queryset should return an empty queryset for an org with no matching rows."""
    # Arrange
    org = OrganizationFactory()

    # Act
    result = BaseMultiTenantService.base_queryset(Client, _StubUser(org))

    # Assert
    assert list(result) == []


def test_build_asset_conditions_map_groups_conditions_by_asset_id():
    """build_asset_conditions_map should group condition values under each asset_id."""
    # Arrange
    audits = [
        _StubAudit(asset_id=1, condition=0),
        _StubAudit(asset_id=1, condition=2),
        _StubAudit(asset_id=2, condition=4),
    ]

    # Act
    result = build_asset_conditions_map(audits)

    # Assert
    assert result[1] == [0, 2]
    assert result[2] == [4]


def test_build_asset_conditions_map_returns_empty_map_for_empty_queryset():
    """build_asset_conditions_map should return an empty mapping when given no audits."""
    # Arrange
    audits = []

    # Act
    result = build_asset_conditions_map(audits)

    # Assert
    assert dict(result) == {}


def test_build_asset_conditions_map_returns_default_empty_list_for_missing_asset_id():
    """build_asset_conditions_map's defaultdict should return [] for an asset_id with no audits."""
    # Arrange
    audits = [_StubAudit(asset_id=1, condition=0)]

    # Act
    result = build_asset_conditions_map(audits)

    # Assert
    assert result[999] == []


class _StubUser:
    """Minimal stand-in exposing only the ``organization`` attribute base_queryset reads."""

    def __init__(self, organization):
        self.organization = organization


class _StubAudit:
    """Minimal stand-in exposing only the ``asset_id``/``condition`` attributes the map reads."""

    def __init__(self, asset_id, condition):
        self.asset_id = asset_id
        self.condition = condition
