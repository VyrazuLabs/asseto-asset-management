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
from assets.models import Asset,AssignAsset
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from .utils import product_list,search_utils,get_product_details,export_product_pdf_utils,added_product,deleted_product,exports_product_csv_utils
import os 
# from silk.profiling.profiler import silk_profile

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
# @silk_profile(name="add_products")
def add_product(request):
    if request.method == "POST":
        form = AddProductsForm(
            request.POST, request.FILES, organization=request.user.organization)
        image_form=ProductImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            added_product(request,form)
            # print("Product added successfully")
            messages.success(request, 'Product added successfully')
            return redirect('products:list')
    else:
        form = AddProductsForm(organization=request.user.organization)
        image_form = ProductImageForm()

    context = {'form': form,
               'image_form': image_form,}
    return render(request, 'products/add.html', context)

@login_required
@permission_required('authentication.delete_product')
def delete_product(request, id):
    if request.method == 'POST':
        get_asset_by_product_id=Asset.objects.filter(product_id=id).first()
        # First find if the product is already assigned to the asset or not
        if AssignAsset.objects.filter(asset=get_asset_by_product_id).exists():
            messages.error(
                request, 'Error! Product is assigned to a Asset')
            # return HttpResponse(status=400)
        else:
            deleted_product(request, id)
            messages.success(request, 'Product deleted successfully')
    return redirect('products:list')
    # return redirect(request.META.get('HTTP_REFERER'))

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
            delete_image_ids = data.get('delete_image_ids', [])
            delete_custom_field_ids = data.get('delete_custom_field_ids', [])
            delete_main_picture = data.get('delete_main_picture', False)
            
            if delete_image_ids:
                ProductImage.objects.filter(id__in=delete_image_ids, product=product).delete()
                return JsonResponse({'success': True, 'message': 'Images deleted successfully.'})
            
            if delete_main_picture:
                if product.product_picture:
                    product.product_picture.delete()
                    product.product_picture = None
                    product.save()
                return JsonResponse({'success': True, 'message': 'Main picture deleted successfully.'})
            
            if delete_custom_field_ids:
                CustomField.objects.filter(entity_id__in=delete_custom_field_ids, object_id=product.id, organization=request.user.organization).delete()
                return JsonResponse({'success': True, 'message': 'Custom fields deleted successfully.'})

            return JsonResponse({'success': False, 'message': 'No IDs provided for deletion.'}, status=400)
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
                key = f"custom_field_{cf.entity_id}"
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
    return render(request, 'products/edit.html', context)


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
    if search_text:
        return render(request, 'products/products-data.html', {
            'page_object': Product.undeleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(manufacturer__icontains=search_text) | Q(product_sub_category__name__icontains=search_text) | Q(product_type__name__icontains=search_text)
            )).annotate(
            total_assets=Count('asset'),
            available_assets=Count('asset', filter=Q(asset__is_assigned=False) and Q(asset__organization=request.user.organization)),
        ).order_by('-created_at'),
        'product_images': product_images
        })
    return render("assets:list")

@login_required
@permission_required('authentication.view_product')
def export_products_csv(request):
    response=exports_product_csv_utils(request)
    return response

@login_required
@permission_required('authentication.view_product')
def export_products_pdf(request):
    response=export_product_pdf_utils(request)
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