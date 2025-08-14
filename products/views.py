from django.shortcuts import render, redirect
from .forms import AddProductsForm,ProductImageForm
from django.contrib import messages
from .models import Product, ProductCategory, ProductType,ProductImage
from django.core.paginator import Paginator
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from vendors.utils import render_to_csv, render_to_pdf
from django.shortcuts import get_object_or_404
from django.db.models import Q,Count


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
                organization=request.user.organization).annotate(
            total_assets=Count('asset'),
            available_assets=Count('asset', filter=Q(asset__is_assigned=False))
        ).order_by('-created_at')
    
    paginator = Paginator(product_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    product_ids_in_page = [product.id for product in page_object]
    images_qs = ProductImage.objects.filter(product_id__in=product_ids_in_page).order_by('uploaded_at')
    print(images_qs)
    
    # Map asset ID to its first image
    product_images = {}
    for img in images_qs:
        if img.product_id not in product_images:
            product_images[img.product_id] = img
            # print("images_product",img)
    for it in product_images:
        print("here",it)
    context = {
        'sidebar': 'products',
        'product_images': product_images,
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
    paginator = Paginator(history_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    get_product_img=ProductImage.objects.filter(product=product).values()
    img_array=[]
    for it in get_product_img:
        img_array.append(it)
    print(img_array)
    context = {
        'sidebar': 'products',
        'product': product,
        'img_array':img_array,
        'title': 'Product - Details',
        'page_object': page_object
    }

    return render(request, 'products/detail.html', context=context)


@login_required
@permission_required('authentication.add_product')
def add_product(request):
    if request.method == "POST":
        form = AddProductsForm(
            request.POST, request.FILES, organization=request.user.organization)
        image_form=ProductImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            product = form.save(commit=False)
            product.organization = request.user.organization
            product.save()
            form.save_m2m()
#             # product = form.save()
            for f in request.FILES.getlist('image'): # 'image' is the name of your file input
                print("imagessssss",f)
                ProductImage.objects.create(product=product, image=f)
            messages.success(request, 'Product added successfully')
            return HttpResponse(status=204)
    else:
        form = AddProductsForm()
        image_form = ProductImageForm()

    context = {'form': form,
               'image_form': image_form,}
    return render(request, 'products/add-product-modal.html', context)
# if form.is_valid() and image_form.is_valid():
#             asset = form.save(commit=False)
#             asset.organization = request.user.organization
#             asset.save()

#             form.save_m2m()
#             # product = form.save()
#             for f in request.FILES.getlist('image'): # 'image' is the name of your file input
#                 print("imagessssss",f)
#                 AssetImage.objects.create(asset=asset, image=f)
#             return redirect('assets:list')

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
