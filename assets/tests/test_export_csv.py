"""Tests for the asset bulk CSV export (``assets:export_csv``).

Covers authentication/permission failures, organisation scoping, the
``assets.all_asset`` scope rule, filter pass-through, soft-delete exclusion
and CSV formula-injection neutralisation.
"""

import csv
import io

import factory
import factory.django
import pytest
from django.core.management import call_command
from django.urls import reverse

from assets.models import Asset, AssignAsset
from common.factories import OrganizationFactory, make_user_with_permissions


@pytest.fixture(autouse=True)
def _synced_permissions(db):
    """Permission rows are written by ``sync_permissions``, not post_migrate."""
    call_command("sync_permissions", verbosity=0)


class _AssetFactory(factory.django.DjangoModelFactory):
    """Local factory for ``Asset``; promote to ``assets/tests/factories.py``
    when another suite needs it."""

    class Meta:
        model = Asset

    tag = factory.Sequence(lambda n: f"TAG-{n:05d}")
    name = factory.Sequence(lambda n: f"Asset {n}")
    organization = factory.SubFactory(OrganizationFactory)


class _AssignAssetFactory(factory.django.DjangoModelFactory):
    """Local factory for ``AssignAsset``."""

    class Meta:
        model = AssignAsset

    asset = factory.SubFactory(_AssetFactory)


def _export(client, **params):
    response = client.get(reverse("assets:export_csv"), params)
    if response.status_code != 200:
        return response, []
    body = b"".join(response.streaming_content).decode()
    return response, list(csv.reader(io.StringIO(body)))


def _tags(rows):
    return {row[0] for row in rows[1:]}


@pytest.mark.django_db
def test_export_csv_returns_header_and_attachment_disposition(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions(
        "assets.view_asset", "assets.all_asset", organization=org
    )
    client.force_login(user)

    # Act
    response, rows = _export(client)

    # Assert
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert response["Content-Disposition"].startswith(
        'attachment; filename="export-assets-'
    )
    assert rows[0] == [
        "Asset Tag",
        "Asset Name",
        "Product",
        "Product Type",
        "Vendor",
        "Location",
        "Client",
        "Status",
    ]


@pytest.mark.django_db
def test_export_csv_excludes_other_organizations_assets(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions(
        "assets.view_asset", "assets.all_asset", organization=org
    )
    own = _AssetFactory(organization=org)
    foreign = _AssetFactory()
    client.force_login(user)

    # Act
    _, rows = _export(client)

    # Assert
    assert _tags(rows) == {own.tag}
    assert foreign.tag not in _tags(rows)


@pytest.mark.django_db
def test_export_csv_excludes_soft_deleted_assets(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions(
        "assets.view_asset", "assets.all_asset", organization=org
    )
    live = _AssetFactory(organization=org)
    deleted = _AssetFactory(organization=org)
    deleted.soft_delete()
    client.force_login(user)

    # Act
    _, rows = _export(client)

    # Assert
    assert _tags(rows) == {live.tag}


@pytest.mark.django_db
def test_export_csv_without_all_asset_permission_only_includes_assigned_assets(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions("assets.view_asset", organization=org)
    assigned = _AssetFactory(organization=org)
    unassigned = _AssetFactory(organization=org)
    _AssignAssetFactory(asset=assigned, user=user)
    client.force_login(user)

    # Act
    _, rows = _export(client)

    # Assert
    assert _tags(rows) == {assigned.tag}
    assert unassigned.tag not in _tags(rows)


@pytest.mark.django_db
def test_export_csv_with_all_asset_permission_includes_unassigned_assets(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions(
        "assets.view_asset", "assets.all_asset", organization=org
    )
    first = _AssetFactory(organization=org)
    second = _AssetFactory(organization=org)
    client.force_login(user)

    # Act
    _, rows = _export(client)

    # Assert
    assert _tags(rows) == {first.tag, second.tag}


@pytest.mark.django_db
def test_export_csv_applies_search_text_filter(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions(
        "assets.view_asset", "assets.all_asset", organization=org
    )
    match = _AssetFactory(organization=org, name="Quantum Laptop")
    _AssetFactory(organization=org, name="Office Chair")
    client.force_login(user)

    # Act
    _, rows = _export(client, search_text="Quantum")

    # Assert
    assert _tags(rows) == {match.tag}


@pytest.mark.django_db
@pytest.mark.parametrize("payload", ["=cmd|' /C calc'!A0", "+1+1", "-2+3", "@SUM(A1)"])
def test_export_csv_prefixes_formula_cells_with_quote(client, payload):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions(
        "assets.view_asset", "assets.all_asset", organization=org
    )
    _AssetFactory(organization=org, name=payload)
    client.force_login(user)

    # Act
    _, rows = _export(client)

    # Assert
    assert rows[1][1] == "'" + payload


@pytest.mark.django_db
def test_export_csv_leaves_plain_cells_untouched(client):
    # Arrange
    org = OrganizationFactory()
    user = make_user_with_permissions(
        "assets.view_asset", "assets.all_asset", organization=org
    )
    _AssetFactory(organization=org, name="Plain Name")
    client.force_login(user)

    # Act
    _, rows = _export(client)

    # Assert
    assert rows[1][1] == "Plain Name"


@pytest.mark.django_db
def test_export_csv_without_any_asset_permission_redirects_to_login(client):
    # Arrange
    user = make_user_with_permissions("support.view_ticket")
    client.force_login(user)

    # Act
    response, _ = _export(client)

    # Assert
    assert response.status_code == 302
    assert "login" in response.url.lower()


@pytest.mark.django_db
def test_export_csv_when_anonymous_redirects_to_login(client):
    # Arrange
    url = reverse("assets:export_csv")

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 302
    assert "login" in response.url.lower() or "next=" in response.url
