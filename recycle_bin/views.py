from itertools import product
from django.shortcuts import render, redirect
from authentication.models import User
from dashboard.models import Department, Location, ProductCategory, ProductType
from vendors.models import Vendor
from assets.models import Asset, AssetStatus
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



@login_required
@user_passes_test(check_admin)
def deleted_locations(request):

    location_list = Location.deleted_objects.filter(Q(
        organization=request.user.organization)|Q(organization=None)).order_by('-updated_at')
    paginator = Paginator(location_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'trash',
        'submenu': 'locations',
        'page_object': page_object,
        'title': 'Deleted location'
    }

    return render(request, 'recycle_bin/deleted-location.html', context=context)


@login_required
@user_passes_test(check_admin)
def deleted_locations_permanently(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                Location.deleted_objects, pk=id, organization=request.user.organization)
            product.delete()
            messages.success(request, 'Location deleted permanently')

    except ProtectedError:

        messages.error(
            request, 'Error! Location is used in asset')

    except:
        messages.error(request, 'Location can not be deleted')

    return redirect('recycle_bin:deleted_locations')


@login_required
@user_passes_test(check_admin)
def deleted_locations_restore(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                Location.deleted_objects, pk=id, organization=request.user.organization)
            product.restore()
            history_id = product.history.first().history_id
            product.history.filter(pk=history_id).update(history_type='^')
            messages.success(request, 'Location restored successfully')

    except:

        messages.error(request, 'Location can not be restored')

    return redirect('recycle_bin:deleted_locations')


@login_required
def deleted_locations_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'recycle_bin/deleted-location-data.html', {
            'page_object': Location.deleted_objects.filter(Q(organization=request.user.organization) & (Q(
                office_name__icontains=search_text) | Q(contact_person_name__icontains=search_text) | Q(contact_person_email__icontains=search_text) | Q(contact_person_phone__icontains=search_text)
                | Q(address__address_line_one__icontains=search_text) | Q(address__address_line_two__icontains=search_text) | Q(address__country__icontains=search_text) | Q(address__state__icontains=search_text)
                | Q(address__city__icontains=search_text) | Q(address__pin_code__icontains=search_text)
            )).order_by('-created_at')[:10]
        })

    location_list = Location.deleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(location_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'recycle_bin/deleted-location-data.html', {'page_object': page_object})


@login_required
@user_passes_test(check_admin)
def deleted_depertments(request):

    department_list = Department.deleted_objects.filter(Q(
        organization=request.user.organization)|Q(organization=None)).order_by('-updated_at')
    paginator = Paginator(department_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'trash',
        'submenu': 'departments',
        'page_object': page_object,
        'title': 'Deleted department'
    }

    return render(request, 'recycle_bin/deleted-department.html', context=context)


@login_required
@user_passes_test(check_admin)
def deleted_departments_permanently(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                Department.deleted_objects, pk=id, organization=request.user.organization)
            product.delete()
            messages.success(request, 'Department deleted permanently')

    except ProtectedError:

        messages.error(
            request, 'Error! Department is used in asset')

    except:
        messages.error(request, 'Department can not be deleted')

    return redirect('recycle_bin:deleted_departments')


@login_required
@user_passes_test(check_admin)
def deleted_departments_restore(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                Department.deleted_objects, pk=id, organization=request.user.organization)
            product.restore()
            history_id = product.history.first().history_id
            product.history.filter(pk=history_id).update(history_type='^')
            messages.success(request, 'Department restored successfully')

    except:

        messages.error(request, 'Location can not be restored')

    return redirect('recycle_bin:deleted_departments')



@login_required
def deleted_departments_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'recycle_bin/deleted-departments-data.html', {
            'page_object': Department.deleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(contact_person_name__icontains=search_text) | Q(contact_person_email__icontains=search_text) | Q(contact_person_phone__icontains=search_text)
            )).order_by('-created_at')[:10]
        })

    department_list = Department.deleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(department_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'recycle_bin/deleted-departments-data.html', {'page_object': page_object})



@login_required
@user_passes_test(check_admin)
def deleted_product_categories(request):

    product_category_list = ProductCategory.deleted_objects.filter(Q(
        organization=request.user.organization)|Q(organization=None)).order_by('-updated_at')
    paginator = Paginator(product_category_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'trash',
        'submenu': 'Prodcut Category',
        'page_object': page_object,
        'title': 'Deleted Product Categories'
    }

    return render(request, 'recycle_bin/deleted-Product-Category.html', context=context)


@login_required
@user_passes_test(check_admin)
def deleted_product_categories_permanently(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                ProductCategory.deleted_objects, pk=id, organization=request.user.organization)
            print(product)
            product.delete()
            messages.success(request, 'Product Category deleted permanently')

    except ProtectedError:

        messages.error(
            request, 'Error! Product Category is used in asset')

    except:
        messages.error(request, 'Product Category can not be deleted')

    return redirect('recycle_bin:deleted_product_categories')


@login_required
@user_passes_test(check_admin)
def deleted_product_categories_restore(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                ProductCategory.deleted_objects, pk=id, organization=request.user.organization)
            print(product)
            product.restore()
            history_id = product.history.first().history_id
            product.history.filter(pk=history_id).update(history_type='^')
            messages.success(request, 'Product Category restored successfully')

    except:

        messages.error(request, 'Product Category can not be restored')

    return redirect('recycle_bin:deleted_product_categories')

@login_required
def search_deleted_product_categories(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'recycle_bin/delete-product-categories-data.html', {
            'page_object': ProductCategory.deleted_objects.filter(Q(organization=request.user.organization) & Q(name__icontains=search_text)).order_by('-created_at')[:10]
        })
    
    product_categories = ProductCategory.deleted_objects.filter(
    organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(product_categories, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'recycle_bin/delete-product-categories-data.html', {'page_object': page_object})


@login_required
@user_passes_test(check_admin)
def deleted_product_types(request):

    product_category_list = ProductType.deleted_objects.filter(Q(
        organization=request.user.organization, can_modify=True)|Q(
        organization=None, can_modify=True)).order_by('-updated_at')
    paginator = Paginator(product_category_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'trash',
        'submenu': 'Prodcut Types',
        'page_object': page_object,
        'title': 'Deleted Product Types'
    }

    return render(request, 'recycle_bin/deleted-Product-types.html', context=context)


@login_required
@user_passes_test(check_admin)
def deleted_product_types_permanently(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                ProductType.deleted_objects, pk=id, organization=request.user.organization)
            print(product)
            product.delete()
            messages.success(request, 'Product Type deleted permanently')

    except ProtectedError:

        messages.error(
            request, 'Error! Product Type is used in asset')

    except:
        messages.error(request, 'Product Type can not be deleted')

    return redirect('recycle_bin:deleted_product_types')


@login_required
@user_passes_test(check_admin)
def deleted_product_types_restore(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                ProductType.deleted_objects, pk=id, organization=request.user.organization)
            print(product)
            product.restore()
            history_id = product.history.first().history_id
            product.history.filter(pk=history_id).update(history_type='^')
            messages.success(request, 'Product Type restored successfully')

    except:

        messages.error(request, 'Product Type can not be restored')

    return redirect('recycle_bin:deleted_product_types')


@login_required
def deleted_product_types_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'recycle_bin/deleted-product-types-data.html', {
            'page_object': ProductType.deleted_objects.filter(Q(organization=request.user.organization) & Q(name__icontains=search_text)).order_by('-created_at')[:10]
        })

    product_type_list = ProductType.deleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(product_type_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'recycle_bin/deleted-product-types-data.html', {'page_object': page_object})


@login_required
@user_passes_test(check_admin)
def deleted_asset_status(request):

    product_category_list = AssetStatus.deleted_objects.filter(Q(
        organization=request.user.organization, can_modify=True)|Q(
        organization=None, can_modify=True)).order_by('-updated_at')
    paginator = Paginator(product_category_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'trash',
        'submenu': 'Asset Status',
        'page_object': page_object,
        'title': 'Deleted Asset Status'
    }

    return render(request, 'recycle_bin/deleted-asset-status.html', context=context)


@login_required
@user_passes_test(check_admin)
def deleted_asset_status_permanently(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                AssetStatus.deleted_objects, pk=id, organization=request.user.organization)
            print(product)
            product.delete()
            messages.success(request, 'Asset Status  deleted permanently')

    except ProtectedError:

        messages.error(
            request, 'Error! Asset Status  is used in asset')

    except:
        messages.error(request, 'Asset Status  can not be deleted')

    return redirect('recycle_bin:deleted_asset_status')


@login_required
@user_passes_test(check_admin)
def deleted_asset_status_restore(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                AssetStatus.deleted_objects, pk=id, organization=request.user.organization)
            print(product)
            product.restore()
            history_id = product.history.first().history_id
            product.history.filter(pk=history_id).update(history_type='^')
            messages.success(request, 'Asset Status  restored successfully')

    except:

        messages.error(request, 'Asset Status can not be restored')

    return redirect('recycle_bin:deleted_asset_status')


@login_required
def deleted_asset_status_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'recycle_bin/deleted-asset-status-data.html', {
            'page_object': AssetStatus.deleted_objects.filter(Q(organization=request.user.organization) & Q(name__icontains=search_text)).order_by('-created_at')[:10]
        })

    status_list = AssetStatus.deleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(status_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'recycle_bin/deleted-asset-status-data.html', {'page_object': page_object})



@login_required
@user_passes_test(check_admin)
def deleted_roles(request):

    product_category_list = AssetStatus.deleted_objects.filter(Q(
        organization=request.user.organization, can_modify=True)|Q(
        organization=None, can_modify=True)).order_by('-updated_at')
    paginator = Paginator(product_category_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'trash',
        'submenu': 'Roles',
        'page_object': page_object,
        'title': 'Deleted Roles'
    }

    return render(request, 'recycle_bin/deleted-roles.html', context=context)


@login_required
@user_passes_test(check_admin)
def deleted_roles_permanently(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                AssetStatus.deleted_objects, pk=id, organization=request.user.organization)
            print(product)
            product.delete()
            messages.success(request, 'Asset Status  deleted permanently')

    except ProtectedError:

        messages.error(
            request, 'Error! Asset Status  is used in asset')

    except:
        messages.error(request, 'Asset Status  can not be deleted')

    return redirect('recycle_bin:deleted_asset_status')


@login_required
@user_passes_test(check_admin)
def deleted_roles_status_restore(request, id):

    try:

        if request.method == 'POST':
            product = get_object_or_404(
                AssetStatus.deleted_objects, pk=id, organization=request.user.organization)
            print(product)
            product.restore()
            history_id = product.history.first().history_id
            product.history.filter(pk=history_id).update(history_type='^')
            messages.success(request, 'Asset Status  restored successfully')

    except:

        messages.error(request, 'Asset Status can not be restored')

    return redirect('recycle_bin:deleted_asset_status')