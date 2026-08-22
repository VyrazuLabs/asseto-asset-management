"""Extension-contributed permission groups for the role-edit modals.

get_extension_permission_groups() feeds the checkbox groups appended to
templates/roles/{add,update}-role-modal.html — same markup, same
"permissions[]" field name as the existing hardcoded groups, so
roles/views.py's save logic needs no changes. See
docs/extension-architecture.md §10.
"""

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from authentication.models import User
from configurations.models import InstalledExtension


def get_extension_permission_groups() -> list:
    """Return one permission group per active extension that declares permissions.

    Returns:
        List of {"label": <extension name>, "permissions": [{"codename", "label"}, ...]}.
    """
    groups = []
    for ext in InstalledExtension.objects.filter(status="active"):
        permissions = ext.manifest_json.get("permissions")
        if not permissions:
            continue
        groups.append({"label": ext.name, "permissions": permissions})
    return groups


def sync_extension_permissions(manifest: dict) -> None:
    """Create/update Django Permission rows for a manifest's declared permissions.

    Called by enable_extension right after migration succeeds, so the
    permissions are assignable through the Roles UI immediately. Reuses
    the exact convention roles/views.py already uses: every custom
    codename in this app is bound to User's ContentType, regardless of
    which feature it belongs to.

    Args:
        manifest: a validated extension manifest dict.
    """
    permissions = manifest.get("permissions") or []
    content_type = ContentType.objects.get_for_model(User)
    for perm in permissions:
        Permission.objects.get_or_create(
            codename=perm["codename"],
            content_type=content_type,
            defaults={"name": f"Can {perm['label']}"},
        )
