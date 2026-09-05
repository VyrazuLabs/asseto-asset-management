from django import template

from common.permissions import ACTION_ICONS, PERMISSION_MODULES

register = template.Library()


@register.filter
def permission_module_matrix(role):
    """Build a per-display-group action matrix for a Role, granted and denied alike.

    For every group the role holds at least one permission in, lists every
    action across every module sharing that group's ``display_group`` (not
    just the granted ones) so denied actions can be shown too. Modules that
    share a ``display_group`` (e.g. Assets + Assign Assets — two different
    models presented as one "Assets" concept) are merged into a single
    entry, instead of one bare action-only badge per permission or one
    fragmented card per underlying model.

    Args:
        role: The ``Role`` instance to build the matrix for.

    Returns:
        list[dict]: One entry per display group the role touches, sorted by
        label, each shaped as ``{"module": str, "actions": list[dict]}``
        where each action dict is ``{"label": str, "icon": str, "granted": bool}``.
    """
    granted_codenames = set(role.permissions.values_list("codename", flat=True))
    grouped_actions = {}

    for module in PERMISSION_MODULES:
        module_codenames = set(module.codenames())
        if not module_codenames & granted_codenames:
            continue

        grouped_actions.setdefault(module.display_group, [])
        grouped_actions[module.display_group].extend(
            {
                "label": action.label,
                "icon": ACTION_ICONS.get(action.action, "bi-dot"),
                "granted": action.codename in granted_codenames,
            }
            for action in module.actions
        )

    entries = [{"module": group, "actions": actions} for group, actions in grouped_actions.items()]
    return sorted(entries, key=lambda entry: entry["module"])
