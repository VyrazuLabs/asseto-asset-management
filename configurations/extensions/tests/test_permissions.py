"""Tests for configurations.extensions.permissions.get_extension_permission_groups.

Feeds the role-modal templates' extension-contributed checkbox groups, per
docs/extension-architecture.md §10.
"""

import pytest

from configurations.extensions.permissions import get_extension_permission_groups
from configurations.models import InstalledExtension


def _extension_with_permissions(name, permissions=None, status="active"):
    manifest = {"name": name, "license_required": False}
    if permissions is not None:
        manifest["permissions"] = permissions
    return InstalledExtension.objects.create(
        name=name,
        app_label=f"ext_{name}",
        version="1.0.0",
        status=status,
        source="local",
        manifest_json=manifest,
    )


@pytest.mark.django_db
def test_returns_empty_when_no_extension_declares_permissions():
    # Arrange
    _extension_with_permissions("no_perms_ext", permissions=None)

    # Act
    groups = get_extension_permission_groups()

    # Assert
    assert groups == []


@pytest.mark.django_db
def test_returns_one_group_per_extension_with_permissions():
    # Arrange
    _extension_with_permissions(
        "sample_extension",
        permissions=[
            {"codename": "view_sample_extension", "label": "View"},
            {"codename": "add_sample_extension", "label": "Add"},
        ],
    )

    # Act
    groups = get_extension_permission_groups()

    # Assert
    assert len(groups) == 1
    assert groups[0]["label"] == "sample_extension"
    assert groups[0]["permissions"] == [
        {"codename": "view_sample_extension", "label": "View"},
        {"codename": "add_sample_extension", "label": "Add"},
    ]


@pytest.mark.django_db
def test_excludes_extensions_not_active():
    # Arrange
    _extension_with_permissions(
        "pending_ext",
        permissions=[{"codename": "view_pending_ext", "label": "View"}],
        status="pending_restart",
    )

    # Act
    groups = get_extension_permission_groups()

    # Assert
    assert groups == []
