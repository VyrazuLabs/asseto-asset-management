from django.shortcuts import render, redirect
from dashboard.models import Location, Address
from dashboard.forms import LocationForm, AddressForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q,Count
from assets.models import AssignAsset,Asset
from dashboard.utils import get_location_list
import os

IS_DEMO = os.environ.get('IS_DEMO')

PAGE_SIZE = 10
ORPHANS = 1


def check_admin(user):
    return user.is_superuser


def manage_access(user):
    permissions_list = [
        'authentication.add_location',
        'authentication.edit_location',
        'authentication.delete_location',
        'authentication.view_location',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False


@login_required
@user_passes_test(manage_access)
def locations(request):
    page_object, location_asset_count, stats = get_location_list(request)
    
    context = {
        'sidebar': 'admin',
        'submenu': 'location',
        'page_object': page_object,
        'location_asset_count': location_asset_count,
        'title': 'Locations',
        **stats
    }

    return render(request, 'dashboard/locations/list.html', context=context)


@login_required
@permission_required('authentication.view_location')
def location_details(request, id):

    location = get_object_or_404(
        Location.undeleted_objects, pk=id, organization=request.user.organization)

    history_list = location.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'sidebar': 'admin', 'submenu': 'location', 'page_object': page_object,
               'location': location, 'title': f'Details-{location. office_name}'}
    return render(request, 'dashboard/locations/detail.html', context=context)


@login_required
@permission_required('authentication.add_location')
def add_location(request):
    address_form = AddressForm(request.POST or None)
    location_form = LocationForm(request.POST or None)

    if request.method == "POST":
        if address_form.is_valid() and location_form.is_valid():
            address = address_form.save()
            location = location_form.save(commit=False)
            location.address = address
            location.organization = request.user.organization
            location.save()
            messages.success(request, 'Location added successfully')
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "locationAdded"
            return response

    context = {
        'address_form': address_form,
        'location_form': location_form,
    }
    return render(request, 'dashboard/locations/add-location-modal.html', context=context)


@login_required
@permission_required('authentication.edit_location')
def update_location(request, id):

    if Location.objects.filter(pk=id).exists():

        location = get_object_or_404(
            Location.undeleted_objects, pk=id, organization=request.user.organization)
        address = get_object_or_404(Address, pk=location.address.id)

        location_form = LocationForm(request.POST or None, instance=location)
        address_form = AddressForm(request.POST or None, instance=address)

        if request.method == "POST":

            if location_form.is_valid() and address_form.is_valid():

                location_form.save()
                address_form.save()
                messages.success(request, 'Location updated successfully')
                return redirect(f'/admin/locations/update/{location.id}')

        context = {'sidebar': 'admin', 'submenu': 'location', 'location_form': location_form,
                   'address_form': address_form, 'location': location, 'title': f'Update-{location. office_name}'}

    else:
        return redirect('/admin/locations/list')

    return render(request, 'dashboard/locations/update-location.html', context=context)

@login_required
@permission_required('authentication.delete_location')
def delete_location(request, id):

    if request.method == 'POST':
        location = get_object_or_404(
            Location.undeleted_objects, pk=id, organization=request.user.organization)
        # Check if the deleted location is assigned to any asset, if yes then unassign the asset before deleting the location
        assigned_assets = AssignAsset.objects.filter(asset__location=location).first()
        if assigned_assets is not None:
            messages.error(request, 'Location cannot be deleted as it is assigned to an asset. Please unassign the asset before deleting the location.')
            return redirect('dashboard:locations')
        location.status = False
        location.soft_delete()
        history_id = location.history.first().history_id
        location.history.filter(pk=history_id).update(history_type='-')
        messages.success(request, 'Location deleted  successfully')
    return redirect('dashboard:locations')

@login_required
@user_passes_test(check_admin)
def location_status(request, id):
    if request.method == "POST":
        location = get_object_or_404(
            Location.undeleted_objects, pk=id, organization=request.user.organization)
        location.status = False if location.status else True
        location.save()
    return HttpResponse(status=204)

@login_required
def search_location(request, page):
    page_object, location_asset_count, stats = get_location_list(request, page_number=page)
    
    return render(request, 'dashboard/locations/locations-data.html', 
                  {'page_object': page_object,
                   'location_asset_count': location_asset_count,
                   **stats
                   })
