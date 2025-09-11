import json
from django.shortcuts import render, redirect
from .forms import AddProductsForm,ProductImageForm
from django.contrib import messages
from .models import Product, ProductCategory, ProductType,ProductImage
from django.core.paginator import Paginator
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from vendors.utils import render_to_csv, render_to_pdf
from django.shortcuts import get_object_or_404
from django.db.models import Q,Count
from dashboard.models import CustomField
from assets.models import AssetImage
from assets.models import Asset
from django.views.decorators.csrf import csrf_exempt
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

    product_list = Product.undeleted_objects.filter(Q(organization=None) | Q(
            organization=request.user.organization)).annotate(
            total_assets=Count('asset'),
            available_assets=Count('asset', filter=Q(asset__is_assigned=False) and Q(asset__organization=request.user.organization)),
        ).order_by('-created_at')
    deleted_product_count=Product.deleted_objects.count()
    paginator = Paginator(product_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    product_ids_in_page = [product.id for product in page_object]
    images_qs = ProductImage.objects.filter(product_id__in=product_ids_in_page).order_by('uploaded_at')
    # Map asset ID to its first image
    product_images = {}
    for img in images_qs:
        if img.product_id not in product_images:
            product_images[img.product_id] = img
    context = {
        'sidebar': 'products',
        'product_images': product_images,
        'page_object': page_object,
        'deleted_product_count':deleted_product_count,
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
    get_custom_data=[]
    get_data=CustomField.objects.filter(object_id=product.id)
    for it in get_data:
        obj={}
        obj['field_name']=it.field_name
        obj['field_value']=it.field_value
        get_custom_data.append(obj)

    context = {
        'sidebar': 'products',
        'product': product,
        'img_array':img_array,
        'title': 'Product - Details',
        'page_object': page_object,
        'get_custom_data': get_custom_data
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
            files=request.FILES
            for f in files.getlist('image'): # 'image' is the name of your file input
                ProductImage.objects.create(product=product, image=f)
            names = request.POST.getlist('custom_field_name')
            values = request.POST.getlist('custom_field_value')
            for key, value in request.POST.items():
                    if key.startswith("customfield_") and value.strip() != "":
                        field_id = key.replace("customfield_", "")
                        try:
                            cf = CustomField.objects.get(pk=field_id, entity_type='asset', organization=request.user.organization)
                            CustomField.objects.create(
                                name=cf.name,
                                object_id=product.id,
                                field_type=cf.field_type,
                                field_name=cf.field_name,
                                field_value=value,
                                entity_type='product',
                                organization=request.user.organization
                            )
                        except CustomField.DoesNotExist:
                            pass

            for name, val in zip(names, values):
                if name.strip() and val.strip():
                    CustomField.objects.create(
                        name=name.strip(),
                        object_id=product.id,
                        field_type='text',  # Defaulting new ones as text unless field type select is added
                        field_name=name.strip(),
                        field_value=val.strip(),
                        entity_type='product',
                        organization=request.user.organization
                    )
            messages.success(request, 'Product added successfully')
            return redirect('products:list')
    else:
        form = AddProductsForm(organization=request.user.organization)
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

@csrf_exempt
@login_required
@permission_required('authentication.edit_product')
def update_product(request, id):
    product = get_object_or_404(
        Product.undeleted_objects, pk=id, organization=request.user.organization)
    form = AddProductsForm(
        instance=product, organization=request.user.organization)
    img_form= ProductImageForm(request.POST, request.FILES)
    get_product_img=ProductImage.objects.filter(product=product).values()
    custom_fields = CustomField.objects.filter(
        entity_type='product', object_id=product.id, organization=request.user.organization)
    img_array=[]
    for it in get_product_img:
        img_array.append(it)

    if request.method=="DELETE":
        try:
            data = json.loads(request.body)
            delete_ids = data.get('delete_image_ids', [])
            if delete_ids:
                ProductImage.objects.filter(id__in=delete_ids, product=product).delete()
                return JsonResponse({'success': True, 'message': 'Images deleted successfully.'})
            else:
                return JsonResponse({'success': False, 'message': 'No image IDs provided.'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)
        
    elif request.method == "POST":
        form = AddProductsForm(request.POST, request.FILES,
        instance=product, organization=request.user.organization)
        img_form= ProductImageForm(request.POST, request.FILES)
        if form.is_valid() and img_form.is_valid():
            form.save()
            images = request.FILES.getlist('image')
            for img_file in images:
                ProductImage.objects.create(product=product, image=img_file)
            custom_fields = CustomField.objects.filter(entity_type='product', object_id=product.id, organization=request.user.organization)
            for cf in custom_fields:
                key = f"custom_field_{cf.entity_id}"
                new_val = request.POST.get(key, "")
                if new_val != cf.field_value:
                    cf.field_value = new_val
                    cf.save()
        #Code to add new custom fields
            for key, value in request.POST.items():
                if key.startswith("customfield_") and value.strip():
                    field_id = key.replace("customfield_", "")
                    try:
                        cf = CustomField.objects.get(
                            pk=field_id,
                            entity_type='asset',
                            organization=request.user.organization
                        )
                        CustomField.objects.create(
                            name=cf.name,
                            object_id=product.id,
                            field_type=cf.field_type,
                            field_name=cf.field_name,
                            field_value=value,
                            entity_type='asset',
                            organization=request.user.organization
                        )
                    except CustomField.DoesNotExist:
                        continue

            # Handle dynamically added custom fields
            names = request.POST.getlist('custom_field_name')
            values = request.POST.getlist('custom_field_value')
            for name, val in zip(names, values):
                if name.strip() and val.strip():
                    CustomField.objects.create(
                        name=name.strip(),
                        object_id=product.id,
                        field_type='text',
                        field_name=name.strip(),
                        field_value=val.strip(),
                        entity_type='asset',
                        organization=request.user.organization
                    )
                    print("Custom Field added successfully 2")   
        messages.success(request, 'Product updated successfully')
        return redirect('products:list')

    context = {'form': form, 'product': product,'product_images': img_array,'img_form':img_form,'custom_fields': custom_fields,}
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

def get_assigned_product_info(request, id):
    product = get_object_or_404(
        Product.undeleted_objects, pk=id, organization=request.user.organization)
    get_assets=Asset.objects.filter(product=product, organization=request.user.organization)
    context = {
        'get_assets': get_assets,
        'title': 'Assigned Product Info',
    }
    return render(request, 'products/assigned-product-modal.html', context=context)