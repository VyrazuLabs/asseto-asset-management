from django.shortcuts import render, redirect
from .forms import UserForm, UserUpdateForm, AddressForm
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from authentication.models import User
from assets.models import AssignAsset
from dashboard.models import Address
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from .utils import create_all_perm_role
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from vendors.utils import render_to_csv, render_to_pdf
from django.db.models import Q
from django.contrib.auth.decorators import permission_required
from datetime import date
from assets.models import Asset,AssetImage
today = date.today()

PAGE_SIZE = 10
ORPHANS = 1


def check_admin(user):
    return user.is_superuser


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


@login_required
@user_passes_test(manage_access)
def list(request):
    users_list = User.undeleted_objects.filter(organization=request.user.organization, is_superuser=False).exclude(
        pk=request.user.id).order_by('-created_at')
    deleted_user_count=User.deleted_objects.count()
    paginator = Paginator(users_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    if request.method == "POST":
        messages.success(
            request, 'User added successfully and Verification email sent to the user')

        return redirect(request.META.get('HTTP_REFERER'))

    context = {'sidebar': 'users',
               'page_object': page_object, 'deleted_user_count':deleted_user_count,'title': 'Users'}
    return render(request, 'users/list.html', context=context)


@login_required
@permission_required('authentication.view_users')
def details(request, id):

    user = get_object_or_404(User.undeleted_objects, pk=id, organization=request.user.organization)
    assigned_assets = AssignAsset.objects.filter(user=user)
    
    
    
    history_list = User.history.all()
    paginator = Paginator(history_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    asset_paginator=Paginator(assigned_assets,10,orphans=1)
    asset_page_number=request.GET.get('assets_page')
    asset_page_object=asset_paginator.get_page(asset_page_number)

    context = {
        'sidebar': 'users',
        'user': user,
        'page_object': page_object,
        'assigned_assets': asset_page_object,
        'title': 'User - Details'
    }
               
    return render(request, 'users/detail.html',context)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # for get_asset in get_assigned_assets:
    #     get_obj['assigned_date']=get_asset['assigned_date']

    # for it in get_assigned_assets:
    #     get_asset_obj=Asset.objects.filter(id=it['asset_id'])
    #     for asset_data in get_asset_obj:
    #         get_obj['vendor']=asset_data.vendor.name if asset_data.vendor else 'N/A'
    #         get_obj['type']=asset_data.product.product_type.name if asset_data.product.product_type else 'N/A'

    #     get_asset=get_asset_obj.values()
    #     for it in get_asset:
    #         get_obj['asset_name']=it['name']
    #         get_obj['serial_no']=it['serial_no']
    #         get_obj['id']=it['id']

    #     assigned_assets.append(get_obj)

 


    


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

            if password1 and password1 == password2:
                user.set_password(password1)
            address = address_form.save()
            user.organization = request.user.organization
            user.address = address
            user.save()
            # form.instance.role.user_set.add(form.instance)
            messages.success(
                request, 'User added successfully and Verification email sent to the user')

            all_perms, created = Group.objects.get_or_create(
                name='all_perms')

            if form.instance.access_level:
                all_perms.user_set.add(form.instance)
            else:
                all_perms.user_set.remove(form.instance)

            return HttpResponse(status=204)

    context = {
        'form': form,
        'address_form': address_form
    }

    return render(request, 'users/add-user-modal.html', context)


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


@user_passes_test(check_admin)
def status(request, id):
    if request.method == "POST":
        user = get_object_or_404(
            User.undeleted_objects, pk=id, organization=request.user.organization)
        user.is_active = False if user.is_active else True
        user.save()

    return HttpResponse(status=204)


@login_required
def search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'users/users-data.html', {
            'page_object': User.undeleted_objects.filter(Q(organization=request.user.organization) & Q(is_superuser=False) & (Q(
                username__icontains=search_text) | Q(full_name__icontains=search_text) | Q(phone__icontains=search_text) | Q(employee_id__icontains=search_text) | Q(department__name__icontains=search_text) | Q(role__related_name__icontains=search_text)
                | Q(location__office_name__icontains=search_text) | Q(address__address_line_one__icontains=search_text) | Q(address__address_line_two__icontains=search_text) | Q(address__country__icontains=search_text) | Q(address__state__icontains=search_text) | Q(address__pin_code__icontains=search_text) | Q(address__city__icontains=search_text)
            )).exclude(pk=request.user.id).order_by('-created_at')[:10]
        })

    user_list = User.undeleted_objects.filter(
        organization=request.user.organization, is_superuser=False).exclude(pk=request.user.id).order_by('-created_at')
    paginator = Paginator(user_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'users/users-data.html', {'page_object': page_object})


@login_required
def export_users_csv(request):
    header_list = ['Name', 'Email', 'Phone', 'Designation', 'Department', 'Address Line One',
                   'Address Line Two', 'City', 'Pin Code', 'State', 'Country', 'Office']
    user_list = User.undeleted_objects.filter(organization=request.user.organization, is_superuser=False).exclude(pk=request.user.id).order_by('-created_at').values_list('full_name', 'email', 'phone', 'role__related_name',
                                                                                                                                                                          'department__name', 'address__address_line_one', 'address__address_line_two', 'address__city', 'address__pin_code', 'address__state', 'address__country', 'location__office_name')
    context = {'header_list': header_list, 'rows': user_list}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="export-users-{today}.csv"'
    return response


@login_required
def export_users_pdf(request):
    users = User.undeleted_objects.filter(organization=request.user.organization, is_superuser=False).exclude(
        pk=request.user.id).order_by('-created_at')
    context = {'users': users}
    pdf = render_to_pdf('users/users-pdf.html', context_dict=context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="export-users-{today}.pdf"'
    return response

@login_required
def user_assigned_assets(request, id):
    # user = get_object_or_404(User.undeleted_objects, pk=id, organization=request.user.organization)
    get_user=AssignAsset.objects.filter(user_id=id)
    return render(request, 'users/assigned-asset-modal.html', {'get_user': get_user})