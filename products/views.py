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
from .utils import product_list,get_product_details,added_product,deleted_product
import os 

IS_DEMO = os.environ.get('IS_DEMO')
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
    context=product_list(request)
    return render(request, 'products/list.html', context=context)

@login_required
@permission_required('authentication.view_product')
def details_product(request, id):
    context=get_product_details(request,id)
    return render(request, 'products/detail.html', context=context)

@login_required
@permission_required('authentication.add_product')
def add_product(request):
    if request.method == "POST":
        form = AddProductsForm(
            request.POST, request.FILES, organization=request.user.organization)
        image_form=ProductImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            added_product(request,form)
            print("Product added successfully")
            messages.success(request, 'Product added successfully')
            return redirect('products:list')
    else:
        form = AddProductsForm(organization=request.user.organization)
        image_form = ProductImageForm()

    context = {'form': form,
               'image_form': image_form,}
    return render(request, 'products/add-product-modal.html', context)

@login_required
@permission_required('authentication.delete_product')
def delete_product(request, id):
    if request.method == 'POST':
        deleted_product(request, id)
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
    get_product_img=ProductImage.objects.filter(product=product).order_by('-uploaded_at').values()
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
        form = AddProductsForm(
            request.POST,
            request.FILES,
            instance=product,
            organization=request.user.organization
        )
        img_form = ProductImageForm(request.POST, request.FILES)

        if form.is_valid() and img_form.is_valid():
            product = form.save(commit=False)
            product.audit_interval = form.cleaned_data.get("audit_interval") or 0
            product.organization = request.user.organization
            product.save()
            form.save_m2m()

            for img_file in request.FILES.getlist("image"):
                ProductImage.objects.create(product=product, image=img_file)

            # Update existing custom fields
            for cf in custom_fields:
                key = f"custom_field_{cf.id}"
                new_val = request.POST.get(key, "")
                if new_val != cf.field_value:
                    cf.field_value = new_val
                    cf.save()

            # Add new custom fields
            for key, value in request.POST.items():
                if key.startswith("customfield_") and value.strip():
                    field_id = key.replace("customfield_", "")
                    try:
                        original = CustomField.objects.get(
                            pk=field_id,
                            entity_type="product",
                            organization=request.user.organization
                        )
                        CustomField.objects.create(
                            name=original.name,
                            object_id=product.id,
                            field_type=original.field_type,
                            field_name=original.field_name,
                            field_value=value,
                            entity_type="product",
                            organization=request.user.organization,
                        )
                    except CustomField.DoesNotExist:
                        continue

            # Add dynamically created fields
            names = request.POST.getlist("custom_field_name")
            values = request.POST.getlist("custom_field_value")

            for name, val in zip(names, values):
                if name.strip() and val.strip():
                    CustomField.objects.create(
                        name=name.strip(),
                        object_id=product.id,
                        field_type="text",
                        field_name=name.strip(),
                        field_value=val.strip(),
                        entity_type="product",  # FIXED!
                        organization=request.user.organization,
                    )

            messages.success(request, "Product updated successfully")
            return redirect(f"/products/details/{product.id}")

    context = {'form': form, 'title': f'Edit - {product.name}','product': product,'product_images': img_array,'img_form':img_form,'custom_fields': custom_fields,}
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
                name__icontains=search_text) | Q(manufacturer__icontains=search_text) | Q(product_sub_category__name__icontains=search_text) | Q(product_type__name__icontains=search_text)
            )).annotate(
            total_assets=Count('asset'),
            available_assets=Count('asset', filter=Q(asset__is_assigned=False) and Q(asset__organization=request.user.organization)),
        ).order_by('-created_at')
        })

    product_list = Product.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(product_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    product_ids_in_page = [product.id for product in page_object]
    images_qs = ProductImage.objects.filter(product_id__in=product_ids_in_page).order_by('uploaded_at')
    # Map asset ID to its first image
    product_images = {}
    for img in images_qs:
        if img.product_id not in product_images:
            product_images[img.product_id] = img
    return render(request, 'products/list.html', {'page_object': page_object})


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