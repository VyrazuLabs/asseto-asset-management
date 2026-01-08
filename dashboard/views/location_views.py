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
    location_list = Location.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    deleted_location_count=Location.deleted_objects.count()
    paginator = Paginator(location_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    asset_counts = (
        Asset.objects
        .filter(organization=request.user.organization,
                location__in=location_list)
        .values("location")
        .annotate(asset_count=Count("id"))
    )
    # is_demo=IS_DEMO
    # if is_demo:
    #     is_demo=True
    # else:
    #     is_demo=False
    location_asset_count = {item["location"]: item["asset_count"] for item in asset_counts}
    context = {
        'sidebar': 'admin',
        'submenu': 'location',
        'page_object': page_object,
        'deleted_location_count':deleted_location_count,
        'location_asset_count':location_asset_count,
        'title': 'Locations',
        # 'is_demo':is_demo
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
            return HttpResponse(status=204)

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
                return redirect(f'/admin/locations/details/{location.id}')

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
        location.status = False
        location.soft_delete()
        history_id = location.history.first().history_id
        location.history.filter(pk=history_id).update(history_type='-')
        messages.success(request, 'Location deleted  successfully')
    return redirect('dashboard:locations')


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
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'dashboard/locations/locations-data.html', {
            'page_object': Location.undeleted_objects.filter(Q(organization=request.user.organization) & (Q(
                office_name__icontains=search_text) | Q(contact_person_name__icontains=search_text) | Q(contact_person_email__icontains=search_text) | Q(contact_person_phone__icontains=search_text)
                | Q(address__address_line_one__icontains=search_text) | Q(address__address_line_two__icontains=search_text) | Q(address__country__icontains=search_text) | Q(address__state__icontains=search_text)
                | Q(address__city__icontains=search_text) | Q(address__pin_code__icontains=search_text)
            )).order_by('-created_at')[:10]
        })

    location_list = Location.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(location_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    asset_counts = (
        Asset.objects
        .filter(organization=request.user.organization,
                location__in=location_list)
        .values("location")
        .annotate(asset_count=Count("id"))
    )
    location_asset_count = {item["location"]: item["asset_count"] for item in asset_counts}
    return render(request, 'dashboard/locations/locations-data.html', 
                  {'page_object': page_object,
                   'location_asset_count':location_asset_count
                   })
