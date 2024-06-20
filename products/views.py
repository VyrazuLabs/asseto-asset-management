from django.shortcuts import render, redirect
from .forms import AddProductsForm
from django.contrib import messages
from .models import Product, ProductCategory, ProductType
from django.core.paginator import Paginator
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from vendors.utils import render_to_csv, render_to_pdf
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
        'authentication.view_product',
        'authentication.delete_product',
        'authentication.edit_product',
        'authentication.add_product',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False


@login_required
@user_passes_test(manage_access)
def list(request):

    product_list = Product.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(product_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'products',
        'page_object': page_object,
        'title': 'Products'
    }

    return render(request, 'products/list.html', context=context)


@login_required
@permission_required('authentication.view_product')
def details_product(request, id):

    product = get_object_or_404(
        Product.undeleted_objects, pk=id, organization=request.user.organization)

    history_list = product.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'products',
        'product': product,
        'title': 'Product - Details',
        'page_object': page_object
    }

    return render(request, 'products/detail.html', context=context)


@login_required
@permission_required('authentication.add_product')
def add_product(request):
    form = AddProductsForm(organization=request.user.organization)

    if request.method == "POST":
        form = AddProductsForm(
            request.POST, request.FILES, organization=request.user.organization)

        if form.is_valid():
            product = form.save(commit=False)
            product.organization = request.user.organization
            product.save()
            messages.success(request, 'Product added successfully')
            return HttpResponse(status=204)

    context = {'form': form}
    return render(request, 'products/add-product-modal.html', context)


@login_required
@permission_required('authentication.delete_product')
def delete_product(request, id):

    if request.method == 'POST':
        product = get_object_or_404(
            Product.undeleted_objects, pk=id, organization=request.user.organization)
        product.status = False
        product.soft_delete()
        history_id = product.history.first().history_id
        product.history.filter(pk=history_id).update(history_type='-')
        messages.success(request, 'Product deleted successfully')

    return redirect(request.META.get('HTTP_REFERER'))


@login_required
@permission_required('authentication.edit_product')
def update_product(request, id):

    product = get_object_or_404(
        Product.undeleted_objects, pk=id, organization=request.user.organization)
    form = AddProductsForm(
        instance=product, organization=request.user.organization)

    if request.method == "POST":
        form = AddProductsForm(request.POST, request.FILES,
                               instance=product, organization=request.user.organization)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully')
            return HttpResponse(status=204)

    context = {'form': form, 'product': product}
    return render(request, 'products/update-product-modal.html', context)


@user_passes_test(check_admin)
def status(request, id):
    if request.method == "POST":
        product = get_object_or_404(
            Product.undeleted_objects, pk=id, organization=request.user.organization)
        product.status = False if product.status else True
        product.save()
    return HttpResponse(status=204)


@login_required
def search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'products/products-data.html', {
            'page_object': Product.undeleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(manufacturer__icontains=search_text) | Q(product_category__name__icontains=search_text) | Q(product_type__name__icontains=search_text)
            )).order_by('-created_at')[:10]
        })

    product_list = Product.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(product_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'products/products-data.html', {'page_object': page_object})


@login_required
@permission_required('authentication.view_product')
def export_products_csv(request):
    header_list = ['Product Name', 'Product Category',
                   'Product Type', 'Manufacturer', 'Description']
    product_list = Product.undeleted_objects.filter(organization=request.user.organization).order_by(
        '-created_at').values_list('name', 'product_category__name', 'product_type__name', 'manufacturer', 'description')
    context = {'header_list': header_list, 'rows': product_list}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="export-products-{today}.csv"'
    return response


@login_required
@permission_required('authentication.view_product')
def export_products_pdf(request):
    products = Product.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    context = {'products': products}
    pdf = render_to_pdf('products/products-pdf.html', context_dict=context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="export-products-{today}.pdf"'
    return response
