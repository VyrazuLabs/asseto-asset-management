from django.shortcuts import render, redirect
from dashboard.forms import ProductTypeForm
from django.contrib import messages
from dashboard.models import ProductType
from django.core.paginator import Paginator
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q


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

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False

@login_required
@user_passes_test(manage_access)
def product_type_list(request):
    all_product_type_list = ProductType.undeleted_objects.filter(
    Q(organization=request.user.organization)|Q(organization=None)).order_by('-created_at')
    deleted_product_types_count=ProductType.deleted_objects.filter(can_modify=True).count()


    paginator = Paginator(all_product_type_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    product_type = ProductTypeForm(organization=request.user.organization)

    context = {
        'sidebar': 'admin',
        'submenu': 'product_type',
        'product_type': product_type,
        'page_object': page_object,
        'deleted_product_types_count':deleted_product_types_count,
        'title': 'Product Types'
    }

    return render(request, 'dashboard/product_type/list.html', context=context)


@login_required
@permission_required('authentication.add_product_type')
def add_product_type(request):

    form = ProductTypeForm(organization=request.user.organization)

    if request.method == "POST":
        form = ProductTypeForm(
            request.POST, organization=request.user.organization)

        if form.is_valid():
            pt = form.save(commit=False)
            pt.organization = request.user.organization
            pt.save()
            messages.success(
                request, 'Product Type added successfully')
            return HttpResponse(status=204)

    context = {'form': form, "modal_title": "Add Product Type"}
    return render(request, 'dashboard/product_type/product-type-modal.html', context)


@login_required
@user_passes_test(check_admin)
def product_type_details(request, id):

    product_type = get_object_or_404(
        ProductType.undeleted_objects, pk=id, organization=request.user.organization)

    history_list = product_type.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'sidebar': 'admin', 'page_object': page_object,
               'submenu': 'product_type', 'product_type': product_type, 'title': 'Product Type - Details'}
    return render(request, 'dashboard/product_type/detail.html', context=context)


@login_required
@permission_required('authentication.delete_product_type')
def delete_product_type(request, id):

    if request.method == 'POST':
        product_type = get_object_or_404(
            ProductType.undeleted_objects, pk=id, organization=request.user.organization)
        product_type.status = False
        product_type.soft_delete()
        history_id = product_type.history.first().history_id
        product_type.history.filter(pk=history_id).update(history_type='-')
        messages.success(request, 'Product Type deleted successfully')
    return redirect(request.META.get('HTTP_REFERER'))


@user_passes_test(check_admin)
def product_type_status(request, id):
    if request.method == "POST":
        product_type = get_object_or_404(
            ProductType.undeleted_objects, pk=id, organization=request.user.organization)
        product_type.status = False if product_type.status else True
        product_type.save()
    return HttpResponse(status=204)


@login_required
@permission_required('authentication.edit_product_type')
def update_product_type(request, id):

    product_type = get_object_or_404(
        ProductType.undeleted_objects, pk=id, organization=request.user.organization)
    form = ProductTypeForm(request.POST or None, instance=product_type,
                           organization=request.user.organization,   pk=product_type.id)

    if request.method == "POST":

        if form.is_valid():
            form.save()
            messages.success(request, 'Product Type updated successfully')
            return HttpResponse(status=204)

    context = {'form': form, "modal_title": "Update Product Type"}
    return render(request, 'dashboard/product_type/product-type-modal.html', context)


@login_required
def search_product_type(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'dashboard/product_type/product-types-data.html', {
            'page_object': ProductType.undeleted_objects.filter(Q(organization=request.user.organization) & Q(name__icontains=search_text)).order_by('-created_at')[:10]
        })

    product_type_list = ProductType.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(product_type_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'dashboard/product_type/product-types-data.html', {'page_object': page_object})
