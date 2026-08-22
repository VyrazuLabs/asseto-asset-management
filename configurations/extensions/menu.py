"""Sidebar menu items contributed by active extensions.

Reads each active InstalledExtension's manifest "sidebar" block and
filters to what the given user has permission for, reusing the existing
flat User-ContentType permission convention (every custom codename in
this app is checked as "authentication.<codename>" regardless of feature
— see roles/views.py). See docs/extension-architecture.md §10.
"""

from configurations.models import InstalledExtension


def get_extension_menu_items(user) -> list:
    """Return sidebar items for active extensions the user can see.

    Args:
        user: the requesting user.

    Returns:
        List of {"label", "icon", "url_name", "slug"} dicts, sorted by the
        manifest's "sidebar.order". Extensions with no "sidebar" block, or
        not currently active, contribute nothing.
    """
    items = []
    for ext in InstalledExtension.objects.filter(status="active"):
        sidebar = ext.manifest_json.get("sidebar")
        if not sidebar:
            continue
        permission = sidebar.get("permission")
        if permission and not user.has_perm(f"authentication.{permission}"):
            continue
        items.append(
            {
                "label": sidebar["label"],
                "icon": sidebar.get("icon", "bi bi-puzzle"),
                "url_name": sidebar["url_name"],
                "slug": ext.name,
                "order": sidebar.get("order", 0),
            }
        )
    items.sort(key=lambda item: item["order"])
    return items
