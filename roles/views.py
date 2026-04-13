from django.shortcuts import render, redirect
from roles.models import Role
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.models import Permission, Group
from authentication.models import User
from django.contrib.contenttypes.models import ContentType
from uuid import uuid4
from django.contrib.auth.decorators import user_passes_test
from .forms import RoleForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .utils import get_roles_list_utils
from django.db.models import Q

PAGE_SIZE = 10
ORPHANS = 1


def check_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(check_admin)
def list(request):
    page_number = request.GET.get('page', 1)
    page_object, role_user_count, stats = get_roles_list_utils(request, page_number)

    context = {
        'sidebar': 'admin',
        'submenu': 'roles',
        'page_object': page_object,
        'role_user_count': role_user_count,
        'total_roles': stats['total_roles'],
        'active_roles': stats['active_roles'],
        'inactive_roles': stats['inactive_roles'],
        'deleted_roles_count': stats['deleted_roles_count'],
        'title': 'Roles'
    }
    return render(request, 'roles/list.html', context=context)


@login_required
@user_passes_test(check_admin)
def add(request):
    form = RoleForm(request.POST or None,
    organization=request.user.organization)

    if request.method == 'POST':
        if form.is_valid():
            role = form.save(commit=False)
            role.name = uuid4().hex
            role.organization = request.user.organization
            role.save()

            permissions = request.POST.getlist('permissions[]')
            content_type = ContentType.objects.get_for_model(User)

            role.permissions.clear()

            for codename in permissions:

                temp_name = codename.split('_')
                name = ''

                for ele in temp_name:
                    name += ele+' '

                permission, created = Permission.objects.get_or_create(
                    codename=codename, name=f'Can {name}', content_type=content_type)

                role.permissions.add(permission)

            response = HttpResponse(status=204)
            response["HX-Trigger"] = "roleAdded"
            return response

    context = {'form': form}
    return render(request, 'roles/add-role-modal.html', context=context)


@login_required
@user_passes_test(check_admin)
def update(request, name):
    role = get_object_or_404(
        Role, name=name, organization=request.user.organization)
    form = RoleForm(request.POST or None, instance=role,
                    organization=request.user.organization, pk=role.id)
    permissions = role.permissions.values_list('codename', flat=True)

    if request.method == 'POST':

        if form.is_valid():
            form.save()

            permissions = request.POST.getlist('permissions[]')
            role.permissions.clear()
            content_type = ContentType.objects.get_for_model(User)

            for codename in permissions:

                temp_name = codename.split('_')
                name = ''

                for ele in temp_name:
                    name += ele+' '

                permission, created = Permission.objects.get_or_create(
                    codename=codename, name=f'Can {name}', content_type=content_type)

                role.permissions.add(permission)

            response = HttpResponse(status=204)
            response["HX-Trigger"] = "roleUpdated"
            return response

    context = {
        'form': form,
        'permissions': permissions
    }
    return render(request, 'roles/update-role-modal.html', context=context)


@login_required
@user_passes_test(check_admin)
def delete(request, name):
    if request.method == 'POST':
        role = get_object_or_404(
            Role, name=name, organization=request.user.organization)
        try:
            role.delete()
            messages.success(request, 'Role deleted successfully')
        except:
            messages.error(
                request, 'Error! Role is assigned to a user')
    return redirect('roles:list')


@user_passes_test(check_admin)
def status(request, name):
    if request.method == "POST":
        role = get_object_or_404(
            Role, name=name, organization=request.user.organization)
        role.status = False if role.status else True
        role.save()
    return HttpResponse(status=204)


@login_required
def search(request, page):
    page_object, role_user_count, stats = get_roles_list_utils(request, page)

    return render(request, 'roles/roles-data.html', {
        'page_object': page_object,
        'role_user_count': role_user_count,
        'total_roles': stats['total_roles'],
    })
