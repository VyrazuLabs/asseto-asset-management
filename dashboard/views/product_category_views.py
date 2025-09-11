from django.shortcuts import render, redirect
from dashboard.forms import ProductCategoryForm
from django.contrib import messages
from dashboard.models import ProductCategory, ProductType
from django.core.paginator import Paginator
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse

PAGE_SIZE = 10
ORPHANS = 1


def check_admin(user):
    return user.is_superuser


def manage_access(user):
    permissions_list = [
        'authentication.delete_product_category',
        'authentication.edit_product_category',
        'authentication.add_product_category',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False


@login_required
@user_passes_test(manage_access)
def product_category_list(request):

    all_product_category_list = ProductCategory.undeleted_objects.filter( Q(organization=None)|
    Q(organization=request.user.organization)).order_by('-created_at').exclude(name='Root')

    deleted_product_categories_count=ProductCategory.deleted_objects.filter( Q(organization=None)|
    Q(organization=request.user.organization)).count()

    print(deleted_product_categories_count)
    paginator = Paginator(all_product_category_list,
    PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'admin',
        'submenu': 'product_category',
        'page_object': page_object,
        'deleted_product_categories_count': deleted_product_categories_count,
        'title': 'Product Categories'
    }
    return render(request, 'dashboard/product_category/list.html', context=context)


@login_required
@permission_required('authentication.add_product_category')
def add_product_category(request):
    form = ProductCategoryForm(organization=request.user.organization)

    if request.method == "POST":
        form = ProductCategoryForm(
            request.POST, organization=request.user.organization)

        if form.is_valid():
            pc = form.save(commit=False)
            pc.organization = request.user.organization
            pc.save()
            messages.success(
                request, 'Product Category added successfully')
            return HttpResponse(status=204)

    context = {'form': form, "modal_title": "Add Product Category"}
    return render(request, 'dashboard/product_category/product-category-modal.html', context)


@login_required
@user_passes_test(check_admin)
def product_category_details(request, id):

    product_category = get_object_or_404(
        ProductCategory.undeleted_objects, pk=id, organization=request.user.organization)

    history_list = product_category.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'sidebar': 'admin', 'page_object': page_object,
               'submenu': 'product_category', 'product_category': product_category, 'title': 'Product Category - Details'}
    return render(request, 'dashboard/product_category/detail.html', context=context)


@login_required
@permission_required('authentication.delete_product_category')
def delete_product_category(request, id):

    if request.method == 'POST':
        product_category = get_object_or_404(
            ProductCategory.undeleted_objects, pk=id, organization=request.user.organization)
        product_category.status = False
        product_category.soft_delete()
        history_id = product_category.history.first().history_id
        product_category.history.filter(pk=history_id).update(history_type='-')
        messages.success(request, 'Product Category deleted successfully')

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
@permission_required('authentication.edit_product_category')
def update_product_category(request, id):

    product_category = get_object_or_404(
        ProductCategory.undeleted_objects, pk=id, organization=request.user.organization)
    form = ProductCategoryForm(request.POST or None, instance=product_category,
    organization=request.user.organization,  pk=product_category.id)

    if request.method == "POST":

        if form.is_valid():
            form.save()
            messages.success(request, 'Product Category updated successfully')
            return HttpResponse(status=204)

    context = {'form': form, "modal_title": "Update Product Category"}
    return render(request, 'dashboard/product_category/product-category-modal.html', context)


@user_passes_test(check_admin)
def product_category_status(request, id):
    if request.method == "POST":
        product_category = get_object_or_404(
            ProductCategory.undeleted_objects, pk=id, organization=request.user.organization)
        product_category.status = False if product_category.status else True
        product_category.save()
    return HttpResponse(status=204)


@login_required
def search_product_category(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'dashboard/product_category/product-categories-data.html', {
            'page_object': ProductCategory.undeleted_objects.filter(Q(organization=request.user.organization) & Q(name__icontains=search_text)).order_by('-created_at')[:10]
        })

    product_categories = ProductCategory.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(product_categories, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'dashboard/product_category/product-categories-data.html', {'page_object': page_object})


def get_subcategories(request):
    category_id = request.GET.get('category_id')
    if category_id:
        subcategories = ProductCategory.objects.filter(parent_id=category_id)
        data = [{'id': sub.id, 'name': sub.name} for sub in subcategories]
    else:
        data = []
    return JsonResponse(data, safe=False)
