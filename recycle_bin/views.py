from itertools import product
from django.shortcuts import render, redirect
from authentication.models import User
from vendors.models import Vendor
from assets.models import Asset
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import ProtectedError
from products.models import Product
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q

PAGE_SIZE = 10
ORPHANS = 1


def check_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(check_admin)
def deleted_vendors(request):
    vendors_list = Vendor.deleted_objects.filter(
        organization=request.user.organization).order_by('-updated_at')
    paginator = Paginator(vendors_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'trash',
        'submenu': 'vendors',
        'page_object': page_object,
        'title': 'Deleted Vendors'
    }

    return render(request, 'recycle_bin/deleted-vendors.html', context=context)


@login_required
@user_passes_test(check_admin)
def deleted_vendor_restore(request, id):
    try:
        if request.method == 'POST':
            vendor = get_object_or_404(
                Vendor.deleted_objects, pk=id, organization=request.user.organization)
            vendor.restore()
            history_id = vendor.history.first().history_id
            vendor.history.filter(pk=history_id).update(history_type='^')
            messages.success(request, 'Vendor restored successfully')
    except:
        messages.error(request, 'Vendor can not be restored')

    return redirect('recycle_bin:deleted_vendors')


@login_required
@user_passes_test(check_admin)
def deleted_vendor_permanently(request, id):
    try:
        if request.method == 'POST':
            vendor = get_object_or_404(
                Vendor.deleted_objects, pk=id, organization=request.user.organization)
            vendor.delete()
            messages.success(request, 'Vendor deleted permanently')
    except ProtectedError:
        messages.error(
            request, 'Error! Vendor is used in asset')
    except:
        messages.error(request, 'Vendor can not be deleted')

    return redirect('recycle_bin:deleted_vendors')


@login_required
def deleted_vendors_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'recycle_bin/deleted-vendors-data.html', {
            'page_object': Vendor.deleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(email__icontains=search_text) | Q(phone__icontains=search_text) | Q(designation__icontains=search_text) | Q(gstin_number__icontains=search_text) | Q(contact_person__icontains=search_text)
            )).order_by('-updated_at')[:10]
        })

    vendor_list = Vendor.deleted_objects.filter(
        organization=request.user.organization).order_by('-updated_at')
    paginator = Paginator(vendor_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'recycle_bin/deleted-vendors-data.html', {'page_object': page_object})


@login_required
@user_passes_test(check_admin)
def deleted_products(request):

    products_list = Product.deleted_objects.filter(
        organization=request.user.organization).order_by('-updated_at')
    paginator = Paginator(products_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'trash',
        'submenu': 'products',
        'page_object': page_object,
        'title': 'Deleted Products'
    }

    return render(request, 'recycle_bin/deleted-products.html', context=context)


@login_required
@user_passes_test(check_admin)
def deleted_products_permanently(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                Product.deleted_objects, pk=id, organization=request.user.organization)
            product.delete()
            messages.success(request, 'Product deleted permanently')

    except ProtectedError:

        messages.error(
            request, 'Error! Product is used in asset')

    except:
        messages.error(request, 'Product can not be deleted')

    return redirect('recycle_bin:deleted_products')


@login_required
@user_passes_test(check_admin)
def deleted_products_restore(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                Product.deleted_objects, pk=id, organization=request.user.organization)
            product.restore()
            history_id = product.history.first().history_id
            product.history.filter(pk=history_id).update(history_type='^')
            messages.success(request, 'Product restored successfully')

    except:

        messages.error(request, 'Product can not be restored')

    return redirect('recycle_bin:deleted_products')


@login_required
def deleted_products_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'recycle_bin/deleted-products-data.html', {
            'page_object': Product.deleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(manufacturer__icontains=search_text) | Q(product_category__name__icontains=search_text) | Q(product_type__name__icontains=search_text)
            )).order_by('-updated_at')[:10]
        })

    product_list = Product.deleted_objects.filter(
        organization=request.user.organization).order_by('-updated_at')
    paginator = Paginator(product_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'recycle_bin/deleted-products-data.html', {'page_object': page_object})


@login_required
@user_passes_test(check_admin)
def deleted_assets(request):

    asset_list = Asset.deleted_objects.filter(
        organization=request.user.organization).order_by('-updated_at')
    paginator = Paginator(asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'trash',
        'submenu': 'assets',
        'page_object': page_object,
        'title': 'Deleted Assets'
    }
    return render(request, 'recycle_bin/deleted-assets.html', context=context)


@login_required
@user_passes_test(check_admin)
def deleted_asset_restore(request, id):
    try:
        if request.method == 'POST':
            asset = get_object_or_404(
                Asset.deleted_objects, pk=id, organization=request.user.organization)
            asset.restore()
            history_id = asset.history.first().history_id
            asset.history.filter(pk=history_id).update(history_type='^')
            messages.success(request, 'Asset restored successfully')
    except:
        messages.error(request, 'Asset can not be restored')

    return redirect('recycle_bin:deleted_assets')


@login_required
@user_passes_test(check_admin)
def deleted_asset_permanently(request, id):
    try:
        if request.method == 'POST':
            asset = get_object_or_404(
                Asset.deleted_objects, pk=id, organization=request.user.organization)
            asset.delete()
            messages.success(request, 'Asset deleted permanently')
    except:
        messages.error(request, 'Asset can not be deleted')

    return redirect('recycle_bin:deleted_assets')


@login_required
def deleted_assets_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'recycle_bin/deleted-assets-data.html', {
            'page_object': Asset.deleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(serial_no__icontains=search_text) | Q(purchase_type__icontains=search_text) | Q(product__name__icontains=search_text)
                | Q(vendor__name__icontains=search_text) | Q(vendor__gstin_number__icontains=search_text) | Q(location__office_name__icontains=search_text) | Q(product__product_type__name__icontains=search_text)
            )).order_by('-updated_at')[:10]
        })

    asset_list = Asset.deleted_objects.filter(
        organization=request.user.organization).order_by('-updated_at')
    paginator = Paginator(asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'recycle_bin/deleted-assets-data.html', {'page_object': page_object})


@login_required
@user_passes_test(check_admin)
def deleted_users(request):
    user_list = User.deleted_objects.filter(
        organization=request.user.organization).order_by('-updated_at')
    paginator = Paginator(user_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'trash',
        'submenu': 'users',
        'page_object': page_object,
        'title': 'Deleted Users'
    }

    return render(request, 'recycle_bin/deleted-users.html', context=context)


@login_required
@user_passes_test(check_admin)
def deleted_user_restore(request, id):
    try:
        if request.method == 'POST':
            user = get_object_or_404(
                User.deleted_objects, pk=id, organization=request.user.organization)
            user.restore()
            messages.success(request, 'User restored successfully')
    except:
        messages.error(request, 'User can not be restored')

    return redirect('recycle_bin:deleted_users')


@login_required
@user_passes_test(check_admin)
def deleted_user_permanently(request, id):
    try:
        if request.method == 'POST':
            user = get_object_or_404(
                User.deleted_objects, pk=id, organization=request.user.organization)
            user.delete()
            messages.success(request, 'User deleted permanently')
    except:
        messages.error(request, 'User can not be deleted')

    return redirect('recycle_bin:deleted_users')


@login_required
def deleted_users_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'recycle_bin/deleted-users-data.html', {
            'page_object': User.deleted_objects.filter(Q(organization=request.user.organization) & (Q(
                username__icontains=search_text) | Q(full_name__icontains=search_text) | Q(phone__icontains=search_text) | Q(employee_id__icontains=search_text) | Q(department__name__icontains=search_text) | Q(role__related_name__icontains=search_text)
                | Q(location__office_name__icontains=search_text) | Q(address__address_line_one__icontains=search_text) | Q(address__address_line_two__icontains=search_text) | Q(address__country__icontains=search_text) | Q(address__state__icontains=search_text) | Q(address__pin_code__icontains=search_text) | Q(address__city__icontains=search_text)
            )).order_by('-updated_at')[:10]
        })

    user_list = User.deleted_objects.filter(
        organization=request.user.organization).order_by('-updated_at')
    paginator = Paginator(user_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'recycle_bin/deleted-users-data.html', {'page_object': page_object})
