"""Single source of truth for role/permission modules.

Every assignable permission in the app belongs to a ``PermissionModule``
here — the Role editor UI, the ``sync_permissions``/``verify_permission_migration``
management commands, and the ContentType-repoint data migration all read
this registry instead of hand-coding module lists or codenames.

Three modules (``recycle_bin``, ``configurations``, ``extensions``) don't
map to one real model — Recycle Bin is a cross-cutting view over several
soft-deleted models, Configurations spans several settings models (branding,
localization, tags...), and Extensions currently has no backing app code at
all. Each gets a small unmanaged proxy model (see ``recycle_bin/models.py``,
``configurations/models.py``, ``extensions/models.py``) whose only purpose
is giving ``ContentType.objects.get_for_model()`` a stable, real target —
this is a standard Django pattern for permissions unattached to a concrete
table, not a mistake.

Superusers bypass every check here automatically — Django's
``User.has_perm`` returns ``True`` for ``is_superuser`` before consulting
any of this. Non-superusers fall back strictly to their role's permissions.
"""

from dataclasses import dataclass, field
from functools import wraps
from typing import Sequence

from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied


@dataclass(frozen=True)
class PermissionAction:
    """One assignable action within a module (e.g. "view", "add")."""

    action: str
    codename: str
    label: str


@dataclass(frozen=True)
class PermissionModule:
    """One permission-granting unit, backed by a real (or proxy) model.

    Each module maps to exactly one ContentType — required for correct
    Permission rows — but several modules can share one ``display_group``
    to render as a single card/chip (e.g. Assets + Assign Assets: two
    different models, one user-facing "Assets" concept). Defaults to
    ``label`` when a module isn't part of a larger group.
    """

    key: str
    label: str
    app_label: str
    model_name: str
    actions: Sequence[PermissionAction] = field(default_factory=tuple)
    display_group: str = ""

    def __post_init__(self):
        if not self.display_group:
            object.__setattr__(self, "display_group", self.label)

    def codenames(self) -> list:
        """Return every codename declared for this module."""
        return [a.codename for a in self.actions]


def _crud(app_label: str, model_name: str, noun: str) -> list:
    """Build the standard view/add/edit/delete action set for a module.

    Args:
        app_label: Real Django app label owning the target model.
        model_name: Real model name (lowercase, as Django resolves it).
        noun: Human-readable singular noun used in codenames/labels,
            e.g. "client" -> view_client/add_client/edit_client/delete_client.

    Returns:
        list[PermissionAction]: The four standard CRUD actions.
    """
    return [
        PermissionAction("view", f"view_{noun}", "View"),
        PermissionAction("add", f"add_{noun}", "Add"),
        PermissionAction("edit", f"edit_{noun}", "Edit"),
        PermissionAction("delete", f"delete_{noun}", "Delete"),
    ]


PERMISSION_MODULES: list = [
    PermissionModule("clients", "Clients", "clients", "client", _crud("clients", "client", "client")),
    PermissionModule("vendors", "Vendors", "vendors", "vendor", _crud("vendors", "vendor", "vendor")),
    PermissionModule("products", "Products", "products", "product", _crud("products", "product", "product")),
    PermissionModule("users", "Users", "authentication", "user", _crud("authentication", "user", "users")),
    PermissionModule(
        "assets",
        "Assets",
        "assets",
        "asset",
        [
            *_crud("assets", "asset", "asset"),
            # Scope modifier, not a CRUD action: without it a non-superuser
            # only sees assets currently assigned to them (via AssignAsset);
            # with it they see every asset in the org. Checked in
            # assets/utils.py's filtered_asset().
            PermissionAction("scope", "all_asset", "All Records"),
        ],
    ),
    PermissionModule(
        "assign_assets",
        "Assign Assets",
        "assets",
        "assignasset",
        [
            # Matches templates/roles/update-role-modal.html exactly — that
            # modal (not this registry) is still the only place these get
            # assigned until Phase 3 makes it data-driven, so the action
            # set here must mirror its actual checkboxes, not the fuller
            # set originally proposed in the RBAC overhaul plan.
            # NOTE: codename is "delete_assign_asset" (pre-existing name)
            # but the modal's own label (trans.perm_unassign) calls it
            # "Unassign" — it removes an assignment, not the asset itself.
            # Labeled/iconed as "unassign" here to match what's shown.
            PermissionAction("add", "add_assign_asset", "Add"),
            PermissionAction("reassign", "reassign_assign_asset", "Reassign"),
            PermissionAction("unassign", "delete_assign_asset", "Unassign"),
        ],
        display_group="Assets",
    ),
    PermissionModule(
        "gate_pass",
        "Gate Pass",
        "gate_pass",
        "gatepass",
        [
            # Modal only exposes View/Add today — Edit/Delete/Authorise/
            # Checkout are real gate_pass actions but not yet assignable
            # anywhere, so they're left out until Phase 3/4 wires them up.
            PermissionAction("view", "view_gate_pass", "View"),
            PermissionAction("add", "add_gate_pass", "Add"),
        ],
    ),
    PermissionModule("locations", "Locations", "dashboard", "location", _crud("dashboard", "location", "location")),
    PermissionModule(
        "departments",
        "Departments",
        "dashboard",
        "department",
        # No "view" checkbox in the modal for this module — see note above.
        [a for a in _crud("dashboard", "department", "department") if a.action != "view"],
    ),
    PermissionModule(
        "product_type",
        "Product Types",
        "dashboard",
        "producttype",
        [a for a in _crud("dashboard", "producttype", "product_type") if a.action != "view"],
    ),
    PermissionModule(
        "product_category",
        "Product Categories",
        "dashboard",
        "productcategory",
        [a for a in _crud("dashboard", "productcategory", "product_category") if a.action != "view"],
    ),
    PermissionModule(
        "support_ticket",
        "Support Ticket",
        "support",
        "supportticket",
        [
            *_crud("support", "supportticket", "ticket"),
            # Scope modifier, not a CRUD action: without it a non-superuser
            # only sees tickets assigned to them; with it they see every
            # ticket in the org. Checked in
            # support/utils.py's SupportTicketService.base_queryset().
            PermissionAction("scope", "all_ticket", "All Records"),
        ],
    ),
    # NOTE: "Extensions" was a Role-editor checkbox with no backing app at
    # all (no models, no gated views) — dropped from the registry rather
    # than inventing a new Django app mid-refactor. Re-add once a real
    # extensions app exists to gate.
    PermissionModule("upload", "Upload", "upload", "upload", _crud("upload", "upload", "upload")),
    PermissionModule("license", "License", "license", "license", _crud("license", "license", "license")),
    # New modules — decisions #1/#2 of the RBAC overhaul plan.
    PermissionModule("roles", "Roles", "roles", "role", _crud("roles", "role", "role")),
    PermissionModule(
        "recycle_bin",
        "Recycle Bin",
        "recycle_bin",
        "recyclebinpermission",
        [
            PermissionAction("view", "view_recycle_bin", "View"),
            PermissionAction("restore", "restore_recycle_bin", "Restore"),
            PermissionAction("delete", "delete_recycle_bin", "Permanently Delete"),
        ],
    ),
    PermissionModule("audit", "Audit", "audit", "audit", _crud("audit", "audit", "audit")),
    PermissionModule(
        "notifications", "Notifications", "notifications", "notification", _crud("notifications", "notification", "notification")
    ),
    PermissionModule(
        "custom_fields",
        "Custom Fields",
        "custom_fields",
        "customfielddefinition",
        _crud("custom_fields", "customfielddefinition", "custom_field"),
    ),
    PermissionModule(
        "configurations",
        "Configurations",
        "configurations",
        "configurationpermission",
        _crud("configurations", "configurationpermission", "configuration"),
    ),
]


def get_module(key: str) -> PermissionModule:
    """Look up a ``PermissionModule`` by its ``key``.

    Args:
        key: The module's stable slug (e.g. "clients").

    Returns:
        PermissionModule: The matching module.

    Raises:
        KeyError: If no module with that key is registered.
    """
    for module in PERMISSION_MODULES:
        if module.key == key:
            return module
    raise KeyError(f"No PermissionModule registered for key={key!r}")


def get_content_type_for_module(module: PermissionModule) -> ContentType:
    """Resolve the real ``ContentType`` backing a module.

    Args:
        module: The module to resolve.

    Returns:
        ContentType: The ContentType for ``module.app_label``/``module.model_name``.
    """
    model = apps.get_model(module.app_label, module.model_name)
    return ContentType.objects.get_for_model(model)


# Bootstrap Icons class per action, matching the icon set already used
# elsewhere in the app (see templates/roles/roles-data.html's bi-pencil /
# bi-trash3 row-action buttons). Actions without an explicit entry fall
# back to a generic bullet in the template.
ACTION_ICONS = {
    "view": "bi-eye",
    "add": "bi-plus-lg",
    "edit": "bi-pencil",
    "delete": "bi-trash3",
    "reassign": "bi-arrow-repeat",
    "unassign": "bi-x-circle",
    "authorise": "bi-shield-check",
    "checkout": "bi-box-arrow-right",
    "scope": "bi-globe2",
}


def codename_to_display() -> dict:
    """Build a ``{codename: (module_label, action_label)}`` lookup.

    Used to render a role's permissions grouped by module (e.g. "Clients:
    View, Add") instead of one bare action-only badge per permission, which
    loses which module each permission actually governs.

    Returns:
        dict[str, tuple[str, str]]: Codename to (module label, action label).
    """
    return {
        action.codename: (module.label, action.label)
        for module in PERMISSION_MODULES
        for action in module.actions
    }


def codename_to_app_label() -> dict:
    """Build a ``{codename: app_label}`` lookup across every module.

    Used by the ContentType-repoint migration and by mechanical
    find/replace passes converting ``"authentication.<codename>"`` strings
    to their real ``"<app_label>.<codename>"`` form.

    Returns:
        dict[str, str]: Codename to owning app_label.
    """
    return {action.codename: module.app_label for module in PERMISSION_MODULES for action in module.actions}


def has_any_permission(user, *codenames: str) -> bool:
    """True if ``user`` holds at least one of the given fully-qualified codenames.

    Superusers already short-circuit ``True`` via Django's own
    ``has_perm`` — no special-casing needed here.

    Args:
        user: The user to check (``request.user``).
        *codenames: Fully-qualified permission strings, e.g.
            ``"clients.view_client"``.

    Returns:
        bool: Whether the user has any of the listed permissions.
    """
    return any(user.has_perm(codename) for codename in codenames)


def require_any_permission(*codenames: str):
    """Decorator factory gating a view behind any of the given permissions.

    Standardizes on a 403 (``PermissionDenied``) for an authenticated user
    lacking every listed permission, matching ``@permission_required(...,
    raise_exception=True)``'s behavior — unlike a bare
    ``@user_passes_test``, which redirects to the login page even for an
    already-authenticated, merely-unauthorized user.

    Args:
        *codenames: Fully-qualified permission strings; the view is
            reachable if the user has at least one of them.

    Returns:
        Callable: A decorator to apply to a view function, stacked under
        ``@login_required``.
    """

    def decorator(view_func):
        # user_passes_test always redirects on failure; raise PermissionDenied
        # directly instead so an authenticated-but-unauthorized user gets a
        # 403, matching @permission_required(..., raise_exception=True).
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not has_any_permission(request.user, *codenames):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
