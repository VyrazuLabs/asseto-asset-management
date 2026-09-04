from django import template

from common.permissions import ACTION_ICONS, PERMISSION_MODULES

register = template.Library()


@register.filter
def permission_module_matrix(role):
    """Build a per-module action matrix for a Role, granted and denied alike.

    For every module the role holds at least one permission in, lists
    every action that module defines (not just the granted ones) so denied
    actions can be shown too (e.g. greyed/red), instead of a flat badge
    list that only ever showed what was granted.

    Args:
        role: The ``Role`` instance to build the matrix for.

    Returns:
        list[dict]: One entry per module the role touches, sorted by
        label, each shaped as ``{"module": str, "actions": list[dict]}``
        where each action dict is ``{"label": str, "icon": str, "granted": bool}``.
    """
    granted_codenames = set(role.permissions.values_list("codename", flat=True))
    entries = []

    for module in PERMISSION_MODULES:
        module_codenames = set(module.codenames())
        if not module_codenames & granted_codenames:
            continue

        actions = [
            {
                "label": action.label,
                "icon": ACTION_ICONS.get(action.action, "bi-dot"),
                "granted": action.codename in granted_codenames,
            }
            for action in module.actions
        ]
        entries.append({"module": module.label, "actions": actions})

    return sorted(entries, key=lambda entry: entry["module"])
