from assets.models import Asset, AssignAsset
from dashboard.models import CustomField
from products.models import ProductImage
from django.db.models import Q,Count
from django.core.paginator import Paginator
from products.models import Product
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect,get_object_or_404
from vendors.utils import render_to_csv,render_to_pdf
from datetime import date
import os
from django.http import HttpResponse, JsonResponse

PAGE_SIZE = 10
ORPHANS = 1

def search_utils(request,page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'products/products-data.html', {
            'page_object': Product.undeleted_objects.filter(Q(organization=request.user.organization) & (Q(
                name__icontains=search_text) | Q(manufacturer__icontains=search_text) | Q(product_sub_category__name__icontains=search_text) | Q(product_type__name__icontains=search_text)
            )).annotate(
            total_assets=Count('asset'),
            # available_assets=Count('asset', filter=Q(asset__is_assigned=False) and Q(asset__organization=request.user.organization)),
            available_assets=Count('asset',filter=Q(asset__is_assigned=False) & Q(asset__organization=request.user.organization))
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

    return page_object

def export_product_pdf_utils(request):
    today=date.today()
    products = Product.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    context = {'products': products}
    pdf = render_to_pdf('products/products-pdf.html', context_dict=context)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="export-products-{today}.pdf"'
    return response

def exports_product_csv_utils(request):
    today=date.today()
    header_list = ['Product Name', 'Product Category',
                   'Product Type', 'Manufacturer', 'Description']
    product_list = Product.undeleted_objects.filter(organization=request.user.organization).order_by(
        '-created_at').values_list('name', 'product_category__name', 'product_type__name', 'manufacturer', 'description')
    context = {'header_list': header_list, 'rows': product_list}
    response = render_to_csv(context_dict=context)
    response['Content-Disposition'] = f'attachment; filename="export-products-{today}.csv"'
    return response

def product_list(request):
    product_list = Product.undeleted_objects.filter(Q(organization=None) | Q(
            organization=request.user.organization)).annotate(
            total_assets=Count('asset', filter=Q(asset__is_assigned=True) and Q(asset__organization=request.user.organization) and Q(asset__is_deleted=False)),
            available_assets=Count('asset', filter=Q(asset__is_assigned=True) and Q(asset__organization=request.user.organization) and Q(asset__is_deleted=False))
        ).order_by('-created_at')
    deleted_product_count=Product.deleted_objects.count()
    paginator = Paginator(product_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    product_ids_in_page = [product.id for product in page_object]
    images_qs = ProductImage.objects.filter(product_id__in=product_ids_in_page).order_by('-uploaded_at')
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
    return context

def get_product_details(request,id):
    product = get_object_or_404(                        
        Product.undeleted_objects, pk=id, organization=request.user.organization)
    history_list = product.history.all()
    paginator = Paginator(history_list, 10, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    get_product_img=ProductImage.objects.filter(product=product).order_by('-uploaded_at').values()
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
        'title': f'Details-{product.name}',
        'page_object': page_object,
        'get_custom_data': get_custom_data
    }
    return context

def added_product(request,form):
    product = form.save(commit=False)
    product.audit_interval = form.cleaned_data.get('audit_interval') or 0
    product.organization = request.user.organization
    product.save()
    form.save_m2m()
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

def deleted_product(request, id):
    product = get_object_or_404(
            Product.undeleted_objects, pk=id, organization=request.user.organization)
    product.status = False
    product.soft_delete()
    history_id = product.history.first().history_id
    product.history.filter(pk=history_id).update(history_type='-')

def product_search(request,search_text):
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

# def completed_audit(request):
#     thirty_days_ago = datetime.now() - timedelta(days=30)

#     audits = Audit.objects.filter(
#         created_at__gte=thirty_days_ago
#     ).order_by('-created_at')

#     page = request.GET.get('page', 1)
#     paginator = Paginator(audits, 10)
#     audits_page = paginator.get_page(page)

def convert_to_list(request,products):
    current_host=request.get_host()
    product_list=[]
    for product in products:
        product_dict={
            'id':product.id,
            'name':product.name,
            'type':product.product_type.name if product.product_type else None,
            'category':product.product_sub_category.name if product.product_sub_category else None,
            'total_asset':Asset.objects.filter(product=product.id).count(),
            'status':product.status,
        }
        get_product_image=ProductImage.objects.filter(product=product.id).first()
        if get_product_image:
            product_dict['image']=f"http://{current_host}"+get_product_image.image.url
        else:
            product_dict['image']=None
        product_list.append(product_dict)
        
    return product_list

def product_details(request,product):
    current_host=request.get_host()
    product_detail={
        'id':product.id,
        'name':product.name,
        'type':product.product_type.name,
        'type_id':product.product_type.id,
        'category':product.product_sub_category.name if product.product_sub_category.name else None,
        'category_id':product.product_sub_category.id if product.product_sub_category.name else None,
        'parent_category':product.product_sub_category.parent.name if product.product_sub_category else None,
        'parent_category_id':product.product_sub_category.parent.id if product.product_sub_category else None,
        'manufacture':product.manufacturer if product.manufacturer else None,
        'model_name':product. model if product. model else None,
        'status':product.status if product.status else None,
        'eol':product.eol if product.eol else None,
        'description':product.description if product.description else None,
        'asset_count':Asset.undeleted_objects.filter(product=product.id).count()
    }
    get_product_image=ProductImage.objects.filter(product=product.id)
    product_detail['product_images']=image_list=[]
    if get_product_image:
        for product_image in get_product_image:
            obj={}
            # image_list.append(f"http://{current_host}"+product_image.image.url)
            obj['image_path']=f"http://{current_host}"+product_image.image.url
            obj['image_id']=product_image.id
            image_list.append(obj)
    product_detail['product_images']=image_list
    
    product_detail['custom_fields']=custome_fields_list=[]
    get_custom_fields=CustomField.objects.filter(object_id=product.id)
    if get_custom_fields:
        for custom_field in get_custom_fields:
            custom_fields_dict={custom_field.field_name:custom_field.field_value}
            custome_fields_list.append(custom_fields_dict)
        product_detail['custom_fields']=custome_fields_list


    # get_asset=Asset.objects.filter(product=product.id,organization=request.user.organization)
    # asset_list=[]
    # product_detail['assets']=asset_list
    # if get_asset:
    #     for asset in get_asset:
    #         asset_dict={
    #             'id':asset.id,
    #             'name':asset.name,
    #             'status':asset.asset_status.name
    #         }
    #         asset_dict['assigned_user']=None
    #         assigned_user=AssignAsset.objects.get(asset=asset.id)
    #         if assigned_user:
    #             asset_dict['assigned_user']=assigned_user.user.full_name
    #         asset_list.append(asset_dict)

    #     product_detail['assets']=asset_list
    return product_detail

def product_list_for_form(products):
    list=[]
    for product in products:
        products_dict={
            'id':product.id,
            'name':product.name
        }
        list.append(products_dict)
    return list

def delete_product_images(deleted_image_ids):
    for id in deleted_image_ids:
        try:
            ProductImage.objects.filter(id=id).delete()
        except Exception as e:
            print(e)

# def deleted