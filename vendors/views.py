from multiprocessing import context
from django.shortcuts import render, redirect
from .forms import AddressForm, VendorForm
from django.contrib import messages
from .models import Vendor
from django.core.paginator import Paginator
from dashboard.models import Address
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .utils import render_to_csv, render_to_pdf, searched_data
from django.shortcuts import get_object_or_404
from django.db.models import Q
from assets.models import Asset
from vendors.utils import get_count_of_assets
from dashboard.models import CustomField
from datetime import date
from .utils import export_vendors_pdf_utils,vendor_list_util,get_vendor_details,search_utils,export_vendor_csv_utils
import os
# from silk.profiling.profiler import silk_profile

IS_DEMO = os.environ.get('IS_DEMO')

PAGE_SIZE = 10
ORPHANS = 1


def check_admin(user):
    return user.is_superuser


def manage_access(user):
    permissions_list = [
        'authentication.edit_vendor',
        'authentication.add_vendor',
        'authentication.view_vendor',
        'authentication.delete_vendor',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False

"""Get the list of all the vendors"""
@login_required
@user_passes_test(manage_access)
def vendor_list(request):
    context = vendor_list_util(request)
    return render(request, 'vendors/list.html', context=context)

"""Delete the vendor based on id"""
@login_required
@permission_required('authentication.delete_vendor')
def delete_vendor(request, id):
    if request.method == 'POST':
        vendor = get_object_or_404(
            Vendor.undeleted_objects, pk=id, organization=request.user.organization)
        vendor.status = False
        vendor.soft_delete()
        history_id = vendor.history.first().history_id
        vendor.history.filter(pk=history_id).update(history_type='-')
        messages.success(request, 'Vendor deleted  successfully')
    return redirect('vendors:list')

"""Add a new vendor"""
@login_required
@permission_required('authentication.add_vendor')
# @silk_profile(name="add_vendor")
def add_vendor(request):
    vendor_form = VendorForm()
    address_form = AddressForm()
    if request.method == "POST":
        vendor_form = VendorForm(request.POST)
        address_form = AddressForm(request.POST)
        if vendor_form.is_valid() and address_form.is_valid():
            address = address_form.save()
            vendor = vendor_form.save(commit=False)
            vendor.address = address
            vendor.organization = request.user.organization
            vendor.save()
            messages.success(request, 'Vendor added successfully')
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "vendorAdded"
            return response

    context = {'vendor_form': vendor_form, 'address_form': address_form}
    return render(request, 'vendors/add-vendor-modal.html', context=context)

"""Get the details of the vendor based on id"""
@login_required
@permission_required('authentication.view_vendor')
def details(request, id):
    context = get_vendor_details(request, id)
    return render(request, 'vendors/detail.html', context=context)

"""Update the vendor based on id"""
@login_required
@permission_required('authentication.edit_vendor')
# @silk_profile(name="update_vendor")
def update_vendor(request, id):
    vendor = get_object_or_404(
        Vendor.undeleted_objects, pk=id)
    address = Address.objects.get(id=vendor.address.id)
    vendor_form = VendorForm(instance=vendor)
    address_form = AddressForm(instance=address)
    custom_fields = CustomField.objects.filter(entity_type='asset', object_id=vendor.id, organization=request.user.organization)
    if request.method == "POST":
        vendor_form = VendorForm(request.POST, instance=vendor)
        address_form = AddressForm(request.POST, instance=address)
        if vendor_form.is_valid() and address_form.is_valid():
            vendor_form.save()
            address_form.save()
            custom_fields = CustomField.objects.filter(entity_type='asset', object_id=vendor.id, organization=request.user.organization)
            for cf in custom_fields:
                key = f"custom_field_{cf.entity_id}"
                new_val = request.POST.get(key, "")
                if new_val != cf.field_value:
                    cf.field_value = new_val
                    cf.save()
            messages.success(request, 'Vendor updated successfully')
            # return redirect(f'/vendors/details/{vendor.id}')
            context = {'sidebar': 'vendors', 'vendor_form': vendor_form,
               'address_form': address_form, 'vendor': vendor, 'title': f'Update-{vendor.name}','custom_fields': custom_fields}
            return render(request, 'vendors/update-vendor-modal.html', context=context)
    context = {'sidebar': 'vendors', 'vendor_form': vendor_form,
               'address_form': address_form, 'vendor': vendor, 'title': f'Update-{vendor.name}','custom_fields': custom_fields}
    return render(request, 'vendors/update-vendor-modal.html', context=context)

"""Search the vendors based on search text"""
@login_required
def search(request, page):
    page_object, count_array, deleted_vendor_count = search_utils(request, page)
    return render(
        request,
        "vendors/vendors-data.html",
        {
            "sidebar": "vendors",
            "page_object": page_object,
            "count_array": count_array,
            "deleted_vendor_count": deleted_vendor_count,
            "title": "Vendors",
        },
    )

"""Change the status of the vendor based on id"""
@user_passes_test(check_admin)
def status(request, id):
    if request.method == "POST":
        vendor = get_object_or_404(
            Vendor.undeleted_objects, pk=id, organization=request.user.organization)
        vendor.status = False if vendor.status else True
        vendor.save()
    return HttpResponse(status=204)

"""Export Vendors from Database in a CSV File"""
@login_required
@permission_required('authentication.view_vendor')
def export_vendors_csv(request):
    response=export_vendor_csv_utils(request)
    return response

"""Export Vendors from Database in a PDF File"""
@login_required
@permission_required('authentication.view_vendor')
def export_vendors_pdf(request):
    response=export_vendors_pdf_utils(request)
    return response
