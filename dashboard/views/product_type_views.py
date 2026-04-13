from django.shortcuts import render, redirect, get_object_or_404
from dashboard.forms import ProductTypeForm
from django.contrib import messages
from dashboard.models import ProductType
from django.core.paginator import Paginator
from django.contrib.auth.decorators import permission_required, user_passes_test, login_required
from django.http import HttpResponse
from django.db.models import Q, Count
from assets.models import AssignAsset, Asset
from dashboard.utils import get_product_type_list
import os

IS_DEMO = os.environ.get('IS_DEMO')

PAGE_SIZE = 10
ORPHANS = 1


def check_admin(user):
    return user.is_superuser


def manage_access(user):
    permissions_list = [
        'authentication.delete_product_type',
        'authentication.edit_product_type',
        'authentication.add_product_type',
    ]
    return any(user.has_perm(permission) for permission in permissions_list)


# ✅ UPDATED LIST VIEW (USING UTILS)
@login_required
@user_passes_test(manage_access)
def product_type_list(request):
    page_object, product_type_form, product_type_asset_count, stats = get_product_type_list(request)

    context = {
        'sidebar': 'admin',
        'submenu': 'product_type',
        'page_object': page_object,
        'product_type': product_type_form,
        'product_type_asset_count': product_type_asset_count,
        'title': 'Product Types',
        **stats
    }

    return render(request, 'dashboard/product_type/list.html', context)


# ✅ ADD
@login_required
@permission_required('authentication.add_product_type')
def add_product_type(request):
    form = ProductTypeForm(organization=request.user.organization)

    if request.method == "POST":
        form = ProductTypeForm(request.POST, organization=request.user.organization)

        if form.is_valid():
            pt = form.save(commit=False)
            pt.organization = request.user.organization
            pt.save()
            messages.success(request, 'Product Type added successfully')

            response = HttpResponse(status=204)
            response["HX-Trigger"] = "productTypeAdded"
            return response

    return render(request, 'dashboard/product_type/product-type-modal.html', {
        'form': form,
        "modal_title": "Add Product Type"
    })


# ✅ DETAILS
@login_required
@user_passes_test(check_admin)
def product_type_details(request, id):
    product_type = get_object_or_404(ProductType, pk=id)

    history_list = product_type.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'admin',
        'submenu': 'product_type',
        'product_type': product_type,
        'page_object': page_object,
        'title': f'Details-{product_type.name}'
    }

    return render(request, 'dashboard/product_type/detail.html', context)


# ✅ DELETE
@login_required
@permission_required('authentication.delete_product_type')
def delete_product_type(request, id):
    if request.method == 'POST':
        product_type = get_object_or_404(
            ProductType.undeleted_objects,
            pk=id,
            organization=request.user.organization
        )

        assigned_assets = AssignAsset.objects.filter(
            asset__product__product_type=product_type
        ).first()

        if assigned_assets:
            messages.error(
                request,
                'Product Type cannot be deleted as it is assigned to an asset.'
            )
            return redirect('dashboard:product_type_list')

        product_type.status = False
        product_type.soft_delete()

        history_id = product_type.history.first().history_id
        product_type.history.filter(pk=history_id).update(history_type='-')

        messages.success(request, 'Product Type deleted successfully')

    return redirect(request.META.get('HTTP_REFERER'))


# ✅ STATUS TOGGLE
@login_required
@user_passes_test(check_admin)
def product_type_status(request, id):
    if request.method == "POST":
        product_type = get_object_or_404(
            ProductType.undeleted_objects,
            pk=id,
            organization=request.user.organization
        )
        product_type.status = not product_type.status
        product_type.save()

    return HttpResponse(status=204)


# ✅ UPDATE
@login_required
@permission_required('authentication.edit_product_type')
def update_product_type(request, id):
    product_type = get_object_or_404(
        ProductType.undeleted_objects,
        pk=id,
        organization=request.user.organization
    )

    form = ProductTypeForm(
        request.POST or None,
        instance=product_type,
        organization=request.user.organization,
        pk=product_type.id
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, 'Product Type updated successfully')

        response = HttpResponse(status=204)
        response["HX-Trigger"] = "productTypeUpdated"
        return response

    return render(request, 'dashboard/product_type/product-type-modal.html', {
        'form': form,
        "modal_title": "Update Product Type"
    })


# ✅ UPDATED SEARCH (USING UTILS)
@login_required
def search_product_type(request, page):
    page_object, _, product_type_asset_count, _ = get_product_type_list(request, page_number=page)

    return render(request, 'dashboard/product_type/product-types-data.html', {
        'page_object': page_object,
        'product_type_asset_count': product_type_asset_count
    })