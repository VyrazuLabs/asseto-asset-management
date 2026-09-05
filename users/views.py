import os
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from assets.models import AssignAsset
from authentication.models import Technician, User
from configurations.constants import NAME_FORMATS
from configurations.utils import dynamic_display_name
from dashboard.models import Address

from .forms import AddressForm, UserForm, UserUpdateForm
from .utils import (
    assigned_asset_to_user,
    create_user_notification_type_utils,
    export_users_csv_utils,
    export_users_pdf_utils,
    get_user_detail_utils,
    search_user_utils,
    toggle_two_factor_auth_utils,
)

today = date.today()
IS_DEMO = os.environ.get("IS_DEMO")
PAGE_SIZE = 10
ORPHANS = 1

"""Check if the current user is an admin"""


def check_admin(user):
    return user.is_superuser


"""Create a user notification type"""


def create_user_notification_type(request):
    if request.method == "POST":
        # Convert checkbox values to booleans
        create_user_notification_type_utils(request)

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request"})


# Suppose the user disables the 2FA toggle while being logged in using 2FA then the status
# changes to 1, So that next time the user has to again scan the QR for a new OTP.
# Else if the User dosen't scan for a new otp the 2FA method won't be used.
# Similarly if the user enables the 2FA toggle while being logged in using 2FA then the status changes to 1


def toggle_two_factor_auth(request):
    if request.method == "POST":
        # Convert checkbox values to booleans
        toggle_two_factor_auth_utils(request)
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"})


def manage_access(user):
    permissions_list = [
        "authentication.view_users",
        "authentication.delete_users",
        "authentication.edit_users",
        "authentication.add_users",
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False


"""Get the List of All the Users"""


@login_required
@user_passes_test(manage_access)
def list(request):
    # Every org user shows here now, including superusers and the viewer's
    # own row — previously `is_superuser=False` + self-exclude hid both.
    users_list = User.undeleted_objects.filter(
        organization=request.user.organization
    ).order_by("-created_at")

    total_user_count = users_list.count()
    active_user_count = users_list.filter(is_active=True).count()
    deleted_user_count = User.deleted_objects.count()

    paginator = Paginator(users_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    # method to map the assets with each users
    user_asset_map = assigned_asset_to_user(page_object)
    assigned_assets_count = {uid: len(assets) for uid, assets in user_asset_map.items()}
    total_assigned_assets = sum(assigned_assets_count.values())

    context = {
        "sidebar": "users",
        "page_object": page_object,
        "title": "Users",
        "user_asset_map_count": user_asset_map,
        "user_asset_map_count_count": assigned_assets_count,
        "total_user_count": total_user_count,
        "active_user_count": active_user_count,
        "total_assigned_assets": total_assigned_assets,
        "deleted_user_count": deleted_user_count,
        "is_demo": IS_DEMO,
    }
    return render(request, "users/list.html", context=context)


"""Get the User Details based on the User Id"""


@login_required
@permission_required("authentication.view_users")
def details(request, id):
    (
        get_user_full_name,
        user,
        page_object,
        asset_page_object,
        assigned_licenses_object,
        cf_definitions,
        cf_values,
    ) = get_user_detail_utils(request, id)
    context = {
        "sidebar": "users",
        "full_name": get_user_full_name,
        "user": user,
        "page_object": page_object,
        "assigned_assets": asset_page_object,
        "assigned_licenses": assigned_licenses_object,
        "cf_definitions": cf_definitions,
        "cf_values": cf_values,
        "title": f"Details-{user.full_name}",
    }

    return render(request, "users/detail.html", context)


"""Add a New User"""


@login_required
@permission_required("authentication.add_users")
def add(request):
    form = UserForm(organization=request.user.organization)
    address_form = AddressForm()

    if request.method == "POST":
        form = UserForm(
            request.POST, request.FILES, organization=request.user.organization
        )
        address_form = AddressForm(request.POST)

        if form.is_valid() and address_form.is_valid():
            from custom_fields.utils import validate_cf_values, save_values_for_entity
            cf_errors = validate_cf_values(request, "user")
            if cf_errors:
                from custom_fields.utils import get_definitions_for_module
                return render(request, "users/add-user-modal.html", {
                    "form": form,
                    "address_form": address_form,
                    "cf_definitions": get_definitions_for_module(request.user.organization, "user"),
                    "cf_errors": cf_errors,
                })

            user = form.save(commit=False)
            enable_login = request.POST.get("toggle_password") == "on"
            if enable_login:
                password1 = form.cleaned_data.get("password1", "")
                password2 = form.cleaned_data.get("password2", "")
                if password1 == password2:
                    user.set_password(password1)
            else:
                user.set_unusable_password()

            address = address_form.save()
            user.organization = request.user.organization
            user.address = address
            user.is_active = True
            user.save()
            is_technician = request.POST.get("is_technician",None)
            if is_technician=="on":
                Technician.objects.create(user=user)
            save_values_for_entity(request, user.id, "user")
            messages.success(request, "User added successfully")

            if form.instance.role:
                form.instance.role.user_set.add(form.instance)
            return HttpResponse("", status=204)

    from custom_fields.utils import get_definitions_for_module
    cf_definitions = get_definitions_for_module(request.user.organization, "user")
    context = {"form": form, "address_form": address_form, "cf_definitions": cf_definitions, "cf_errors": []}

    return render(request, "users/add-user-modal.html", context)


"""Update a User based on the User Id"""


@login_required
@permission_required("authentication.edit_users")
def update(request, id):
    user = get_object_or_404(
        User.undeleted_objects, pk=id, organization=request.user.organization
    )
    address = get_object_or_404(Address, pk=user.address.id)

    form = UserUpdateForm(instance=user, organization=request.user.organization)
    address_form = AddressForm(instance=address)
    old_email = user.email

    if request.method == "POST":
        form = UserUpdateForm(
            request.POST,
            request.FILES,
            instance=user,
            organization=request.user.organization,
        )
        address_form = AddressForm(request.POST, instance=address)

        if form.is_valid() and address_form.is_valid():
            from custom_fields.utils import validate_cf_values, save_values_for_entity
            cf_errors = validate_cf_values(request, "user")
            if cf_errors:
                from custom_fields.utils import get_definitions_for_module, get_values_for_entity
                is_technician = Technician.objects.filter(user=user).exists()
                return render(request, "users/update-user-modal.html", {
                    "user": user,
                    "form": form,
                    "address_form": address_form,
                    "is_technician": is_technician,
                    "cf_definitions": get_definitions_for_module(request.user.organization, "user"),
                    "cf_values": get_values_for_entity(user.id, get_definitions_for_module(request.user.organization, "user")),
                    "cf_errors": cf_errors,
                })

            # Clear any previously-assigned role's Group membership before
            # re-adding the (possibly changed) selected role, so switching
            # a user's role in this form actually moves their permissions
            # instead of accumulating every role they've ever had.
            form.instance.groups.clear()

            if form.instance.role:
                form.instance.role.user_set.add(form.instance)
                
            new_email = form.cleaned_data["email"]
            if (old_email) != (new_email):
                messages.success(
                    request,
                    "User updated successfully and verification mail has been sent to the new email address",
                )
            else:
                messages.success(request, "User updated successfully")

            form.save()
            address_form.save()

            save_values_for_entity(request, user.id, "user")

            # Handle technician update dynamically
            is_technician = request.POST.get("is_technician", None)
            if is_technician == "on":
                Technician.objects.get_or_create(user=user)
            else:
                Technician.objects.filter(user=user).delete()

            return HttpResponse(status=204)

    is_technician = Technician.objects.filter(user=user).exists()

    from custom_fields.utils import get_definitions_for_module, get_values_for_entity
    cf_definitions = get_definitions_for_module(request.user.organization, "user")
    cf_values = get_values_for_entity(user.id, cf_definitions)

    context = {
        "user": user,
        "form": form,
        "address_form": address_form,
        "is_technician": is_technician,
        "cf_definitions": cf_definitions,
        "cf_values": cf_values,
        "cf_errors": [],
    }
    return render(request, "users/update-user-modal.html", context)


"""Delete a User based on the User Id"""


@login_required
@permission_required("authentication.delete_users")
def delete(request, id):
    if request.method == "POST":
        user = get_object_or_404(
            User.undeleted_objects, pk=id, organization=request.user.organization
        )

        if AssignAsset.objects.filter(user=user).exists():
            messages.error(
                request, "Error! One or more Assets are assigned to this user"
            )
        else:
            user.soft_delete()
            user.is_active = False
            user.save()
            messages.success(request, "User deleted successfully")

    return redirect(request.META.get("HTTP_REFERER"))


"""Change the Status of a User based on the User Id"""


@user_passes_test(check_admin)
def status(request, id):
    if request.method == "POST":
        user = get_object_or_404(User.undeleted_objects, pk=id)
        user.is_active = False if user.is_active else True
        user.save()

    return HttpResponse(status=204)


"""Search for a User based on search text"""


@login_required
def search(request, page):
    (
        page_object,
        deleted_user_count,
        user_asset_map_count,
        user_asset_map_count_count,
    ) = search_user_utils(request, page)
    return render(
        request,
        "users/users-data.html",
        {
            "sidebar": "users",
            "page_object": page_object,
            "deleted_user_count": deleted_user_count,
            "title": "Users",
            "user_asset_map_count": user_asset_map_count,
            "user_asset_map_count_count": user_asset_map_count_count,
        },
    )


@login_required
def export_users_csv(request):
    response = export_users_csv_utils(request)
    return response


@login_required
def export_users_pdf(request):
    response = export_users_pdf_utils(request)
    return response


@login_required
def user_assigned_assets(request, id):
    # user = get_object_or_404(User.undeleted_objects, pk=id, organization=request.user.organization)
    get_user = AssignAsset.objects.filter(user_id=id)
    return render(request, "users/assigned-asset-modal.html", {"get_user": get_user})


def render_format_based_username(request):
    user = request.user
    get_user_full_name = dynamic_display_name(request=request, fullname=user.full_name)
    new_username = {"username": get_user_full_name}
    return JsonResponse(new_username)
