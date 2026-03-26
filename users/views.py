from django.shortcuts import render, redirect
from license.models import AssignLicense
from .forms import UserForm, UserUpdateForm, AddressForm
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from authentication.models import User,UserTotp
from assets.models import AssignAsset
from dashboard.models import Address
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from .utils import assigned_asset_to_user,export_users_pdf_utils,get_user_detail_utils,export_users_csv_utils,search_user_utils,create_user_notification_type_utils, create_all_perm_role, get_all_assigned_license,toggle_two_factor_auth_utils
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from vendors.utils import render_to_csv, render_to_pdf
from django.db.models import Q,Prefetch
from django.contrib.auth.decorators import permission_required
from datetime import date
from assets.models import Asset,AssetImage
from configurations.utils import dynamic_display_name
from configurations.models import LocalizationConfiguration
from configurations.constants import NAME_FORMATS
from django.http import JsonResponse

today = date.today()
import os
IS_DEMO = os.environ.get('IS_DEMO')

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
        print("Toggled 2FA")
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Invalid request"})

def manage_access(user):
    permissions_list = [
        'authentication.view_users',
        'authentication.delete_users',
        'authentication.edit_users',
        'authentication.add_users',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False

"""Get the List of All the Users"""
@login_required
@user_passes_test(manage_access)
def list(request):
    users_list = User.undeleted_objects.filter(is_superuser=False).exclude(pk=request.user.id).order_by('-created_at')
    
    paginator = Paginator(users_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    # method to maop the assets with each users
    user_asset_map=assigned_asset_to_user(page_object)
    assigned_assets_count = {uid: len(assets) for uid, assets in user_asset_map.items()}

    context = {
        'sidebar': 'users',
        'page_object': page_object,
        'title': 'Users',
        'user_asset_map_count':user_asset_map,
        'user_asset_map_count_count':assigned_assets_count,
    }
    return render(request, 'users/list.html', context=context)


"""Get the User Details based on the User Id"""
@login_required
@permission_required('authentication.view_users')
def details(request, id):
    get_user_full_name,user,page_object,asset_page_object,assigned_licenses_object=get_user_detail_utils(request, id)
    context = {
        'sidebar': 'users',
        'full_name': get_user_full_name,
        'user': user,
        'page_object': page_object,
        'assigned_assets': asset_page_object,
        'assigned_licenses': assigned_licenses_object,
        'title': f'Details-{user.full_name}'
    }
               
    return render(request, 'users/detail.html',context)

"""Add a New User"""
@login_required
@permission_required('authentication.add_users')
def add(request):
    form = UserForm(organization=request.user.organization)
    address_form = AddressForm()

    if request.method == "POST":
        create_all_perm_role()
        form = UserForm(request.POST, request.FILES,
        organization=request.user.organization)
        address_form = AddressForm(request.POST)

        if form.is_valid() and address_form.is_valid():
            user = form.save(commit=False)
            password1 = form.cleaned_data.get('password1', '')
            password2 = form.cleaned_data.get('password2', '')

            if password1 == password2:
                user.set_password(password1)
            address = address_form.save()
            user.organization = request.user.organization
            user.address = address
            user.save()
            messages.success(
                request, 'User added successfully')

            all_perms, created = Group.objects.get_or_create(
                name='all_perms')

            if form.instance.access_level:
                all_perms.user_set.add(form.instance)
            else:
                all_perms.user_set.remove(form.instance)
            
            if form.instance.role:
                form.instance.role.user_set.add(form.instance)
            return HttpResponse('',status=204)

    context = {
        'form': form,
        'address_form': address_form
    }

    return render(request, 'users/add-user-modal.html', context)

"""Update a User based on the User Id"""
@login_required
@permission_required('authentication.edit_users')
def update(request, id):
    create_all_perm_role()
    user = get_object_or_404(
        User.undeleted_objects, pk=id, organization=request.user.organization)
    address = get_object_or_404(Address, pk=user.address.id)

    form = UserUpdateForm(
        instance=user, organization=request.user.organization)
    address_form = AddressForm(instance=address)
    old_email = user.email

    if request.method == "POST":
        form = UserUpdateForm(request.POST, request.FILES,
          instance=user, organization=request.user.organization)
        address_form = AddressForm(request.POST, instance=address)

        if form.is_valid() and address_form.is_valid():
            form.instance.access_level
            form.instance.groups.clear()
            form.instance.role.user_set.add(form.instance)
            new_email = form.cleaned_data['email']
            if (old_email) != (new_email):
                messages.success(
                    request, 'User updated successfully and verification mail has been sent to the new email address')
            else:
                messages.success(request, 'User updated successfully')
            form.save()
            address_form.save()

            all_perms, created = Group.objects.get_or_create(
                name='all_perms')

            if form.instance.access_level:
                all_perms.user_set.add(form.instance)
            else:
                all_perms.user_set.remove(form.instance)

            return HttpResponse(status=204)

    context = {'user': user, 'form': form, 'address_form': address_form}
    return render(request, 'users/update-user-modal.html', context)

"""Delete a User based on the User Id"""
@login_required
@permission_required('authentication.delete_users')
def delete(request, id):
    if request.method == "POST":
        user = get_object_or_404(
            User.undeleted_objects, pk=id, organization=request.user.organization)

        if AssignAsset.objects.filter(user=user).exists():
            messages.error(
                request, 'Error! One or more Assets are assigned to this user')
        else:
            user.soft_delete()
            user.is_active = False
            user.save()
            messages.success(request, 'User deleted successfully')

    return redirect(request.META.get('HTTP_REFERER'))

"""Change the Status of a User based on the User Id"""
@user_passes_test(check_admin)
def status(request, id):
    if request.method == "POST":
        user = get_object_or_404(
            User.undeleted_objects, pk=id)
        user.is_active = False if user.is_active else True
        user.save()

    return HttpResponse(status=204)

"""Search for a User based on search text"""
@login_required
def search(request, page):
    page_object, deleted_user_count, user_asset_map_count, user_asset_map_count_count = search_user_utils(request, page)
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
    response=export_users_csv_utils(request)
    return response

@login_required
def export_users_pdf(request):
    response=export_users_pdf_utils(request)
    return response

@login_required
def user_assigned_assets(request, id):
    # user = get_object_or_404(User.undeleted_objects, pk=id, organization=request.user.organization)
    get_user=AssignAsset.objects.filter(user_id=id)
    return render(request, 'users/assigned-asset-modal.html', {'get_user': get_user})

def render_format_based_username(request):
    user = request.user
    get_user_full_name=dynamic_display_name(request=request,fullname=user.full_name)
    new_username={"username":get_user_full_name}
    return JsonResponse(new_username)