import logging
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from common.permissions import codename_to_display, get_content_type_for_codename
from roles.models import Role

from .forms import RoleForm
from .utils import get_roles_list_utils

logger = logging.getLogger(__name__)

PAGE_SIZE = 10
ORPHANS = 1


def _assign_role_permissions(role: Role, codenames: list) -> None:
    """Replace a role's permissions with the given codenames.

    Resolves each codename's real ContentType via the ``common/permissions.py``
    registry instead of gluing every permission to the fake
    ``authentication.User`` ContentType — that old glue is why permission
    checks written against a real app_label (e.g. ``perms.support.view_ticket``)
    stayed false even when a role had the box checked.

    Wrapped in a transaction: this does a clear() followed by N get_or_create
    + add() calls, and a role controls live access — a failure partway
    through must not leave the role holding zero or half its permissions.

    Args:
        role: The Role to update.
        codenames: Permission codenames submitted from the modal's checkboxes.
    """
    display = codename_to_display()

    with transaction.atomic():
        role.permissions.clear()

        for codename in codenames:
            content_type = get_content_type_for_codename(codename)
            if content_type is None:
                # Not declared in PERMISSION_MODULES — skip rather than silently
                # gluing an unknown codename to an arbitrary ContentType.
                logger.warning("Skipping unregistered permission codename %s for role %s", codename, role.name)
                continue

            _, action_label = display.get(codename, (None, codename.replace("_", " ").title()))
            permission, _ = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={"name": f"Can {action_label.lower()}"},
            )
            role.permissions.add(permission)


@login_required
@permission_required("roles.view_role", raise_exception=True)
def list(request):
    page_number = request.GET.get("page", 1)
    page_object, role_user_count, stats = get_roles_list_utils(request, page_number)

    context = {
        "sidebar": "admin",
        "submenu": "roles",
        "page_object": page_object,
        "role_user_count": role_user_count,
        "total_roles": stats["total_roles"],
        "active_roles": stats["active_roles"],
        "inactive_roles": stats["inactive_roles"],
        "deleted_roles_count": stats["deleted_roles_count"],
        "title": "Roles",
    }
    return render(request, "roles/list.html", context=context)


@login_required
@permission_required("roles.add_role", raise_exception=True)
def add(request):
    form = RoleForm(request.POST or None, organization=request.user.organization)

    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                role = form.save(commit=False)
                role.name = uuid4().hex
                role.organization = request.user.organization
                role.save()

                permissions = request.POST.getlist("permissions[]")
                _assign_role_permissions(role, permissions)

            response = HttpResponse(status=204)
            response["HX-Trigger"] = "roleAdded"
            return response

    context = {"form": form}
    return render(request, "roles/add-role-modal.html", context=context)


@login_required
@permission_required("roles.change_role", raise_exception=True)
def update(request, name):
    role = get_object_or_404(Role, name=name, organization=request.user.organization)
    form = RoleForm(
        request.POST or None,
        instance=role,
        organization=request.user.organization,
        pk=role.id,
    )
    permissions = role.permissions.values_list("codename", flat=True)

    if request.method == "POST":

        if form.is_valid():
            with transaction.atomic():
                form.save()

                permissions = request.POST.getlist("permissions[]")
                _assign_role_permissions(role, permissions)

            response = HttpResponse(status=204)
            response["HX-Trigger"] = "roleUpdated"
            return response

    context = {"form": form, "permissions": permissions}
    return render(request, "roles/update-role-modal.html", context=context)


@login_required
@permission_required("roles.delete_role", raise_exception=True)
def delete(request, name):
    if request.method == "POST":
        role = get_object_or_404(
            Role, name=name, organization=request.user.organization
        )
        try:
            role.delete()
            messages.success(request, "Role deleted successfully")
        except:
            messages.error(request, "Error! Role is assigned to a user")
    return redirect("roles:list")


@login_required
@permission_required("roles.change_role", raise_exception=True)
def status(request, name):
    if request.method == "POST":
        role = get_object_or_404(
            Role, name=name, organization=request.user.organization
        )
        role.status = False if role.status else True
        role.save()
    return HttpResponse(status=204)


@login_required
@permission_required("roles.view_role", raise_exception=True)
def search(request, page):
    page_object, role_user_count, stats = get_roles_list_utils(request, page)

    return render(
        request,
        "roles/roles-data.html",
        {
            "page_object": page_object,
            "role_user_count": role_user_count,
            "total_roles": stats["total_roles"],
        },
    )
