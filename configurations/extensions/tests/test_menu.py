"""Tests for configurations.extensions.menu.get_extension_menu_items.

Reads active InstalledExtension rows' manifest "sidebar" blocks, filters
to ones the given user has permission for, sorted by "order". Reuses the
existing flat User-ContentType permission convention (roles/views.py) —
see docs/extension-architecture.md §10.
"""

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from authentication.models import User
from common.factories import UserFactory
from configurations.extensions.menu import get_extension_menu_items
from configurations.models import InstalledExtension


def _extension_with_sidebar(name, order, permission_codename=None, status="active"):
    manifest = {"name": name, "license_required": False}
    if permission_codename:
        manifest["sidebar"] = {
            "label": name,
            "icon": "bi bi-puzzle",
            "url_name": f"ext_{name}:index",
            "permission": permission_codename,
            "order": order,
        }
    return InstalledExtension.objects.create(
        name=name,
        app_label=f"ext_{name}",
        version="1.0.0",
        status=status,
        source="local",
        manifest_json=manifest,
    )


def _grant_permission(user, codename):
    content_type = ContentType.objects.get_for_model(User)
    permission, _ = Permission.objects.get_or_create(codename=codename, content_type=content_type)
    user.user_permissions.add(permission)


@pytest.mark.django_db
def test_returns_empty_when_no_extensions_have_sidebar():
    # Arrange
    user = UserFactory()
    _extension_with_sidebar("no_sidebar_ext", order=1, permission_codename=None)

    # Act
    items = get_extension_menu_items(user)

    # Assert
    assert items == []


@pytest.mark.django_db
def test_excludes_item_when_user_lacks_permission():
    # Arrange — UserFactory always produces a superuser (has_perm always
    # True); flip flags to get a real permission-less user.
    user = UserFactory()
    user.is_superuser = False
    user.is_staff = False
    user.save()
    _extension_with_sidebar("gated_ext", order=1, permission_codename="view_gated_ext")

    # Act
    items = get_extension_menu_items(user)

    # Assert
    assert items == []


@pytest.mark.django_db
def test_includes_item_when_user_has_permission():
    # Arrange
    user = UserFactory()
    _extension_with_sidebar("gated_ext", order=1, permission_codename="view_gated_ext")
    _grant_permission(user, "view_gated_ext")

    # Act
    items = get_extension_menu_items(user)

    # Assert
    assert len(items) == 1
    assert items[0]["label"] == "gated_ext"
    assert items[0]["url_name"] == "ext_gated_ext:index"


@pytest.mark.django_db
def test_excludes_item_from_extension_not_active():
    # Arrange — installed/pending_restart, not yet active
    user = UserFactory()
    _extension_with_sidebar("pending_ext", order=1, permission_codename="view_pending_ext", status="pending_restart")
    _grant_permission(user, "view_pending_ext")

    # Act
    items = get_extension_menu_items(user)

    # Assert
    assert items == []


@pytest.mark.django_db
def test_sorts_items_by_order():
    # Arrange
    user = UserFactory()
    _extension_with_sidebar("second_ext", order=20, permission_codename="view_second_ext")
    _extension_with_sidebar("first_ext", order=10, permission_codename="view_first_ext")
    _grant_permission(user, "view_second_ext")
    _grant_permission(user, "view_first_ext")

    # Act
    items = get_extension_menu_items(user)

    # Assert
    assert [item["label"] for item in items] == ["first_ext", "second_ext"]
