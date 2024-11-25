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
from .utils import render_to_csv, render_to_pdf
from django.shortcuts import get_object_or_404
from django.db.models import Q

from datetime import date
today = date.today()

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


@login_required
@user_passes_test(manage_access)
def vendor_list(request):
    vendors_list = Vendor.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    print(vendors_list.values('address'))
    paginator = Paginator(vendors_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'sidebar': 'vendors',
               'page_object': page_object, 'title': 'Vendors'}
    return render(request, 'vendors/list.html', context=context)


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


@login_required
@permission_required('authentication.add_vendor')
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
            return HttpResponse(status=204)

    context = {'vendor_form': vendor_form, 'address_form': address_form}
    return render(request, 'vendors/add-vendor-modal.html', context=context)


@login_required
@permission_required('authentication.view_vendor')
def details(request, id):
    vendor = get_object_or_404(
        Vendor.undeleted_objects, pk=id, organization=request.user.organization)
    address = Address.objects.get(id=vendor.address.id)

    history_list = vendor.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'sidebar': 'vendors', 'vendor': vendor, 'page_object': page_object,
               'address': address, 'title': 'Vendor - Details'}
    return render(request, 'vendors/detail.html', context=context)


@login_required
@permission_required('authentication.edit_vendor')
def update_vendor(request, id):
    vendor = get_object_or_404(
        Vendor.undeleted_objects, pk=id, organization=request.user.organization)
    address = Address.objects.get(id=vendor.address.id)
    vendor_form = VendorForm(instance=vendor)
    address_form = AddressForm(instance=address)
    if request.method == "POST":
        vendor_form = VendorForm(request.POST, instance=vendor)
        address_form = AddressForm(request.POST, instance=address)
        if vendor_form.is_valid() and address_form.is_valid():
            vendor_form.save()
            address_form.save()
            messages.success(request, 'Vendor updated successfully')
            return redirect('vendors:list')
    context = {'sidebar': 'vendors', 'vendor_form': vendor_form,
               'address_form': address_form, 'vendor': vendor, 'title': 'Vendor - Update'}
    return render(request, 'vendors/update-vendor-modal.html', context=context)


@login_required
def search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'vendors/vendors-data.html', {
            'page_object': Vendor.undeleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(email__icontains=search_text) | Q(phone__icontains=search_text) | Q(designation__icontains=search_text) | Q(gstin_number__icontains=search_text) | Q(contact_person__icontains=search_text)
            )).order_by('-created_at')[:10]
        })

    vendor_list = Vendor.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(vendor_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'vendors/vendors-data.html', {'page_object': page_object})


@user_passes_test(check_admin)
def status(request, id):
    if request.method == "POST":
        vendor = get_object_or_404(
            Vendor.undeleted_objects, pk=id, organization=request.user.organization)
        vendor.status = False if vendor.status else True
        vendor.save()
    return HttpResponse(status=204)


@login_required
@permission_required('authentication.view_vendor')
def export_vendors_csv(request):
    header_list = ['Vendor Name', 'Vendor Email', 'Phone', 'Contact Person Name', 'Designation', 'GSTIN Number',
                   'Address Line One', 'Address Line Two', 'City', 'Pin Code', 'State', 'Country', 'Description']
    vendors_list = Vendor.undeleted_objects.filter(organization=request.user.organization).order_by('-created_at').values_list('name', 'email', 'phone', 'contact_person', 'designation',
                                                                                                                               'gstin_number', 'address__address_line_one', 'address__address_line_two', 'address__city', 'address__pin_code', 'address__state', 'address__country', 'description')
    context = {'header_list': header_list, 'rows': vendors_list}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="export-vendors-{today}.csv"'
    return response


@login_required
@permission_required('authentication.view_vendor')
def export_vendors_pdf(request):
    vendors = Vendor.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    context = {'vendors': vendors}
    pdf = render_to_pdf('vendors/vendors-pdf.html', context_dict=context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="export-vendors-{today}.pdf"'
    return response
