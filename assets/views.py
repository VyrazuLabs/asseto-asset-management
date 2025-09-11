from django.shortcuts import render, redirect
from .forms import AssetForm, AssignedAssetForm,AssignedAssetListForm, ReassignedAssetForm,AssetImageForm,AssetStatusForm
from django.contrib import messages
from .models import Asset, AssetSpecification, AssignAsset,AssetImage,AssetStatus
from django.core.paginator import Paginator
from django.http import HttpResponse,JsonResponse
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Q,Prefetch
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
import json
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.http import HttpResponseRedirect
from django.urls import reverse
from dashboard.models import CustomField
from vendors.models import Vendor
from django.db.models import Count
import json
from products.models import ProductType

def grouper(iterable, n):
    # Groups iterable into chunks of size n
    args = [iter(iterable)] * n
    return list(zip_longest(*args, fillvalue=None))

from itertools import zip_longest
from .models import Asset,AssignAsset
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from authentication.models import User

@login_required
@permission_required('assets.change_asset', raise_exception=True)
def release_asset(request, id):
    asset = get_object_or_404(Asset, pk=id)
    set_asset = AssetStatus.objects.filter(organization=request.user.organization, name='Available').first()
    asset.asset_status = set_asset
    asset.save()
    msg = f"Asset '{asset.name}' has been released and is now Ready To Deploy."
    return JsonResponse({'success': True, 'message': msg})


from django.contrib.auth import get_user_model

@login_required
@permission_required('assets.change_asset', raise_exception=True)
def assign_assets(request, id):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        asset = get_object_or_404(Asset, pk=id, organization=request.user.organization)
        User = get_user_model()
        selected_user = get_object_or_404(User, pk=user_id, is_active=True)
        
        # Create or update the AssignAsset record
        assign_obj, created = AssignAsset.objects.update_or_create(
            asset=asset,
            defaults={'user': selected_user},
        )

        # Mark asset as assigned
        asset.is_assigned = True
        set_asset=AssetStatus.objects.filter(Q(organization=request.user.organization) | Q(organization__isnull=True), name='Assigned').first()
        asset.asset_status=set_asset
        # asset.status = 0  # 0 = 'Assigned' by your STATUS_CHOICES
        asset.save()

        messages.success(request, f"Asset assigned to user.")
        return redirect('assets:list')

    # Optionally, for GET requests, you might want to show a form or a 404 error:
    return redirect('assets:list')
    # form = AssignedAssetForm(request.POST or None,
    #                          organization=request.user.organization)
    # image_form = AssetImageForm(request.POST, request.FILES)
    # if request.method == 'POST':
    #     if form.is_valid():
    #         form.instance.asset.is_assigned = True
    #         # form.instance.asset.status = 0
    #         form.instance.asset.save()
    #         form.save()
    #         for f in request.FILES.getlist('image'): # 'image' is the name of your file input
    #             AssetImage.objects.create(asset=form.instance.asset, image=f)
    #         messages.success(request, 'Asset assigned to user successfully')
    #         return HttpResponse(status=204)
    # else:
    #     form = AssignedAssetForm()
    #     image_form = AssetImageForm()
    # context = {'form': form,'image_form':image_form}
    # return render(request, 'assets/assign-asset-modal.html', context=context)

PAGE_SIZE = 10
ORPHANS = 1


def check_admin(user):
    return user.is_superuser


def manage_access_for_assets(user):
    permissions_list = [
        'authentication.edit_asset',
        'authentication.view_asset',
        'authentication.delete_asset',
        'authentication.add_asset',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False


def manage_access_for_assign_assets(user):
    permissions_list = [
        'authentication.reassign_assign_asset',
        'authentication.add_assign_asset',
        'authentication.delete_assign_asset',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False

def manage_access_for_assets_status(user):
    permissions_list = [
        'authentication.edit_asset_status',
        'authentication.view_asset_status',
        'authentication.delete_asset_status',
        'authentication.add_asset_status',
    ]

    for permission in permissions_list:
        if user.has_perm(permission):
            return True

    return False

@login_required
@user_passes_test(manage_access_for_assets)
def listed(request):
    user_list=User.objects.filter(Q(organization=None) | Q(organization=request.user.organization),is_active=True).order_by('-created_at')
    vendor_list=Vendor.objects.filter(Q(organization=None) | Q(organization=request.user.organization)).order_by('-created_at')
    asset_status_list=AssetStatus.objects.filter(Q(organization=None) | Q(organization=request.user.organization))
    product_type_list=ProductType.objects.filter(Q(organization=None) | Q(organization=request.user.organization)).order_by('-created_at')
    asset_list = Asset.undeleted_objects.filter(Q(organization=None) | Q(
        organization=request.user.organization)).order_by('-created_at')
    deleted_asset_count=Asset.deleted_objects.count()
    get_assigned_asset_list=AssignAsset.objects.filter(Q(asset__in=asset_list) & Q(asset__organization=None) | Q(asset__organization=request.user.organization)).order_by('-assigned_date')
    asset_user_map = {}
    for assign in get_assigned_asset_list:
        if assign.asset_id not in asset_user_map:
            asset_user_map[assign.asset_id] = None
        if assign.user:  # avoid None users
            asset_user_map[assign.asset_id]=assign.user.full_name
    paginator = Paginator(asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    asset_form = AssetForm(organization=request.user.organization)
    assign_asset_form = AssignedAssetForm(organization=request.user.organization)
    reassign_asset_form = ReassignedAssetForm(organization=request.user.organization)
    active_users=User.objects.filter(is_active=True,organization=request.user.organization)
    print(active_users)
    # active_user=[active_users]
    # Gather the first image per asset in the current page
    asset_ids_in_page = [asset.id for asset in page_object]
    images_qs = AssetImage.objects.filter(asset_id__in=asset_ids_in_page).order_by('-uploaded_at')
    
    # Map asset ID to its first image
    asset_images = {}
    for img in images_qs:
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img
    print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzZ",get_assigned_asset_list)
    # print("product_type_list",product_type_list)
    context = {
        'asset_user_map':asset_user_map,
        'product_type_list':product_type_list,
        'asset_status_list':asset_status_list, 
        'user_list':user_list,
        'vendor_list':vendor_list,
        'active_user':active_users,
        'sidebar': 'assets',
        'submenu': 'list',
        'asset_images': asset_images,  # dict {asset.id: first AssetImage instance}
        'page_object': page_object,
        'asset_form': asset_form,
        'assign_asset_form': assign_asset_form,
        'reassign_asset_form': reassign_asset_form,
        'deleted_asset_count':deleted_asset_count,
        'title': 'Assets'
    }

    return render(request, 'assets/list.html', context=context)


@login_required
@permission_required('authentication.view_asset')
def details(request, id):
    asset = Asset.objects.filter(pk=id, organization=request.user.organization).first()
    if asset is None:
        assetSpecifications=AssignAsset.objects.filter(id=id).first()
        asset=assetSpecifications.asset

    assetSpecifications = AssetSpecification.objects.filter(asset=asset)
    img_array=[]
    get_asset_img=AssetImage.objects.filter(asset=asset).order_by('-uploaded_at').values()
    for it in get_asset_img:
        img_array.append(it)

    months_int=asset.product.eol
    today=timezone.now().date()
    eol_date= today+relativedelta(months=months_int) if months_int is not None else None
    arr_size=len(img_array)
    history_list = asset.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    get_custom_data=[]
    get_data=CustomField.objects.filter(object_id=asset.id)
    for it in get_data:
        obj={}
        obj['field_name']=it.field_name
        obj['field_value']=it.field_value
        get_custom_data.append(obj)
    context = {'sidebar': 'assets', 'asset': asset, 'submenu': 'list', 'page_object': page_object,'arr_size':arr_size,
               'assetSpecifications': assetSpecifications, 'title': 'Asset - Details','get_asset_img':img_array,'eol_date':eol_date,'get_custom_data':get_custom_data}
    return render(request, 'assets/detail.html', context=context)


@login_required
@permission_required('authentication.edit_asset')
# def update(request, id):
#     # AssetImageForm
#     asset = get_object_or_404(
#         Asset.undeleted_objects, pk=id, organization=request.user.organization)
#     assetSpecifications = AssetSpecification.objects.filter(asset=asset)
#     form = AssetForm(request.POST or None, instance=asset,
#                      organization=request.user.organization)
#     image_form = AssetImageForm(request.POST or None, request.FILES)
#     if request.method == "POST":

#         if form.is_valid():

#             assetSpecifications.delete()

#             specifications_names = request.POST.getlist(
#                 'specifications_name')

#             specifications_values = request.POST.getlist(
#                 'specifications_value')

#             for name, value in zip(specifications_names, specifications_values):
#                 if name != '' or value != '':
#                     AssetSpecification.objects.create(
#                         asset=asset, name=name, value=value)

#             asset = form.save(commit=False)
#             asset.organization = request.user.organization
#             asset.save()
#             for f in request.FILES.getlist('image'): # 'image' is the name of your file input
#                 AssetImage.objects.create(asset=asset, image=f)

#             messages.success(request, 'Asset updated successfully')
#             return redirect('assets:list')

#     context = {
#         'sidebar': 'assets',
#         'submenu': 'list',
#         'image_form': image_form,
#         'form': form,
#         'asset': asset,
#         'assetSpecifications': assetSpecifications,
#         'title': 'Asset - Update'
#     }
#     return render(request, 'assets/update-assets.html', context=context)
# from django.shortcuts import get_object_or_404, redirect, render
# from .models import Asset, AssetImage
# from .forms import AssetForm, AssetImageForm

def update(request, id):
    asset = get_object_or_404(Asset, pk=id, organization=request.user.organization)
    asset_images = AssetImage.objects.filter(asset=asset)
    assetSpecifications = AssetSpecification.objects.filter(asset=asset)
    if request.method=="DELETE":
        try:
            data = json.loads(request.body)
            delete_ids = data.get('delete_image_ids', [])
            if delete_ids:
                AssetImage.objects.filter(id__in=delete_ids, asset=asset).delete()
                return JsonResponse({'success': True, 'message': 'Images deleted successfully.'})
            else:
                return JsonResponse({'success': False, 'message': 'No image IDs provided.'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)
        
    elif request.method == 'POST':
        form = AssetForm(request.POST, instance=asset, organization=request.user.organization)
        image_form = AssetImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            asset_instance = form.save(commit=False)
            asset_instance.organization = request.user.organization  # always set or preserve
            asset_instance.save()
            form.save_m2m()
            assetSpecifications.delete()
            # Handle new images
            images = request.FILES.getlist('image')
            for img_file in images:
                AssetImage.objects.create(asset=asset, image=img_file)
            custom_fields = CustomField.objects.filter(entity_type='asset', object_id=asset.id, organization=request.user.organization)
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
                            object_id=asset.id,
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
                        object_id=asset.id,
                        field_type='text',
                        field_name=name.strip(),
                        field_value=val.strip(),
                        entity_type='asset',
                        organization=request.user.organization
                    )
                    print("Custom Field added successfully 2")
            # Success message and redirect
            messages.success(request, "Asset updated successfully.")
            return redirect('assets:list')
    else:
        form = AssetForm(instance=asset, organization=request.user.organization)
        image_form = AssetImageForm()
        custom_fields = CustomField.objects.filter(
                entity_type='asset', object_id=asset.id, organization=request.user.organization)
   
    context = {
        'sidebar': 'assets',
        'submenu': 'list',
        'image_form': image_form,
        'asset_images': asset_images,
        'form': form,
        'asset': asset,
        'assetSpecifications': assetSpecifications,
        'title': 'Asset - Update',
        'custom_fields': custom_fields
    }
    return render(request, 'assets/update-assets.html', context)


@login_required
@permission_required('authentication.add_asset')
def add(request):
    # Handle POST
    if request.method == 'POST':
        form = AssetForm(request.POST, organization=request.user.organization_id)
        image_form = AssetImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            asset = form.save(commit=False)
            asset.organization = request.user.organization
            set_asset_status = AssetStatus.objects.filter(
                Q(organization=request.user.organization) | Q(organization__isnull=True),
                name='Available'
            ).first()
            available_status = AssetStatus.objects.filter(
            name='Available'
            ).first()
            asset.asset_status = available_status 
            asset.save()
            form.save_m2m()

            # Save images
            for f in request.FILES.getlist('image'):
                AssetImage.objects.create(asset=asset, image=f)

            # Handle predefined custom fields
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
                            object_id=asset.id,
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
                        object_id=asset.id,
                        field_type='text',
                        field_name=name.strip(),
                        field_value=val.strip(),
                        entity_type='asset',
                        organization=request.user.organization
                    )
            return redirect('assets:list')
    else:
        form = AssetForm(organization=request.user.organization_id)
        image_form = AssetImageForm()

    # Fetch custom fields for display
    custom_fields = CustomField.objects.filter(
        entity_type='asset',
        organization=request.user.organization
    )

    context = {
        'form': form,
        'image_form': image_form,
        'custom_fields': custom_fields,
        'title': 'Add Asset',
    }
    return render(request, 'assets/add.html', context)


@login_required
@permission_required('authentication.delete_asset')
def delete(request, id):

    if request.method == "POST":
        asset = get_object_or_404(
            Asset.undeleted_objects, pk=id, organization=request.user.organization)
        if asset.is_assigned:
            messages.error(
                request, 'Error! Asset is assigned to a user')
        else:
            asset.soft_delete()
            history_id = asset.history.first().history_id
            asset.history.filter(pk=history_id).update(history_type='-')
            messages.success(request, 'Asset deleted successfully.')

    return redirect('assets:list')


@user_passes_test(check_admin)
def status(request, id):
    if request.method == "POST":
        asset = get_object_or_404(
            Asset.undeleted_objects, pk=id, organization=request.user.organization)
        asset.status = False if asset.status else True
        asset.save()
    return HttpResponse(status=204)


@login_required
def search(request, page):
    search_text = (request.GET.get('search_text') or "").strip()
    vendor_id = request.GET.get('vendor')
    status_id = request.GET.get('status')
    user_id = request.GET.get('user')
    product_type_id = request.GET.get('type')

    # Start query
    q = Q(organization=request.user.organization)

    # Apply filters if present
    if search_text:
        q &= (
            Q(name__icontains=search_text) |
            Q(serial_no__icontains=search_text) |
            Q(purchase_type__icontains=search_text) |
            Q(product__name__icontains=search_text) |
            Q(vendor__name__icontains=search_text) |
            Q(vendor__gstin_number__icontains=search_text) |
            Q(location__office_name__icontains=search_text) |
            Q(product__product_type__name__icontains=search_text)
        )

    if vendor_id:
        q &= Q(vendor_id=vendor_id)

    if status_id:
        q &= Q(asset_status_id=status_id)

    # if user_id:
    #     q &= Q(assigned_user_id=user_id)
    
    if product_type_id:
        q &= Q(product__product_type_id=product_type_id)
    print(q)
    # Get assets
    # asset_user_map = {}
    page_object = Asset.undeleted_objects.filter(q).order_by('-created_at')[:10]
    # assigned_qs = AssignAsset.objects.select_related("user").order_by("-assigned_date")

    # page_object = (
    #     Asset.undeleted_objects
    #     .filter(q)
    #     .prefetch_related(Prefetch("assignasset_set", queryset=assigned_qs, to_attr="assignments"))
    #     .order_by("-created_at")[:10]
    # )
    # if user_id:
    #     page_object=AssignAsset.objects.filter(Q(user_id=user_id)).order_by('-assigned_date')
    #     asset_user_map = {}
    #     for assign in get_assigned_asset_list:
    #         if assign.asset_id not in asset_user_map:
    #             asset_user_map[assign.asset_id] = None
    #         if assign.user:  # avoid None users
    #             asset_user_map[assign.asset_id]=assign.user.full_name
    # print(page_object)
    asset_ids = list(page_object.values_list("id", flat=True))
    image_object = AssetImage.objects.filter(
        asset__organization=request.user.organization,
        asset_id__in=asset_ids
    ).order_by('-uploaded_at')
    asset_images = {}
    for img in image_object:
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img
    # if user_id:
    #     assigned_qs = AssignAsset.objects.filter(user_id=user_id).select_related("user").order_by("-assigned_date")
    #     page_object = (
    #         Asset.undeleted_objects
    #         .filter(q, assignasset__user_id=user_id)
    #         .prefetch_related(Prefetch("assignasset_set", queryset=assigned_qs, to_attr="assignments"))
    #         .order_by("-created_at")[:10]
    #     )
    # else:
    if user_id:
        assigned_qs = AssignAsset.objects.filter(user_id=user_id).select_related("user").order_by("-assigned_date")
        page_object = (
            Asset.undeleted_objects
            .filter(q, assignasset__user_id=user_id)
            .prefetch_related(Prefetch("assignasset_set", queryset=assigned_qs, to_attr="assignments"))
            .order_by("-created_at")[:10]
        )
    else:
        page_object = Asset.undeleted_objects.filter(q).order_by("-created_at")[:10]
    return render(request, 'assets/assets-data.html', {
        'page_object': page_object,
        # 'asset_user_map': asset_user_map,
        'asset_images': asset_images
    })


@login_required
@user_passes_test(manage_access_for_assign_assets)
def assigned_list(request):

    assign_asset_list = AssignAsset.objects.filter(
        asset__organization=request.user.organization or None).order_by('-asset__created_at')
    paginator = Paginator(assign_asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'assets',
        'submenu': 'assigned-assets',
        'page_object': page_object,
        'title': 'Assigned Assets'
    }

    return render(request, 'assets/assigned-list.html', context=context)

@login_required
@user_passes_test(manage_access_for_assign_assets)
def unassigned_list(request):

    assign_asset_list = Asset.objects.filter(
        organization=request.user.organization or None,is_assigned=False).order_by('-created_at')
    paginator = Paginator(assign_asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'assets',
        'submenu': 'assigned-assets',
        'page_object': page_object,
        'title': 'Assigned Assets'
    }

    return render(request, 'assets/unassigned-list.html', context=context)


@login_required
@permission_required('authentication.add_assign_asset')
def assign_asset(request):
    if request.method == 'POST':
        form = AssignedAssetForm(request.POST, organization=request.user.organization_id)
        image_form = AssetImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            # Mark the asset as assigned and save
            asset = form.instance.asset
            asset.is_assigned = True
            set_asset_status = AssetStatus.objects.filter(
                Q(organization=request.user.organization) | Q(organization__isnull=True),
                name='Available'
            ).first()
            asset.asset_status = set_asset_status
            asset.save()
            # form.save_m2m()
            form.save()

            # Save uploaded images related to the asset
            for f in request.FILES.getlist('image'):
                AssetImage.objects.create(asset=asset, image=f)

            messages.success(request, 'Asset assigned to user successfully')
            return HttpResponse(status=204)
    else:
        form = AssignedAssetForm(organization=request.user.organization)
        image_form = AssetImageForm()

    context = {
        'form': form,
        'image_form': image_form,
    }
    return render(request, 'assets/assign-asset-modal.html', context)



@login_required
@permission_required('authentication.reassign_assign_asset')
def reassign_asset(request, id):
    assignAsset = get_object_or_404(
        AssignAsset, pk=id, asset__organization=request.user.organization)
    form = ReassignedAssetForm(
        request.POST or None, instance=assignAsset, organization=request.user.organization)
    if request.method == 'POST':
        if form.is_valid():
            form.save()

            messages.success(
                request, 'Asset re-assigned successfully')
            return HttpResponse(status=204)
    context = {'form': form}
    return render(request, 'assets/reassign-asset-modal.html', context=context)


@login_required
@permission_required('authentication.delete_assign_asset')
def delete_assign(request, id):
    if request.method == 'POST':
        assignAsset = get_object_or_404(
            AssignAsset, pk=id, asset__organization=request.user.organization)
        assignAsset.delete()
        assignAsset.asset.is_assigned = False
        # assignAsset.asset.status = 1  # Assuming 1 is 'Available'
        set_asset=AssetStatus.objects.filter(Q(organization=request.user.organization) | Q(organization__isnull=True), name='Available').first()
        assignAsset.asset.asset_status=set_asset
        assignAsset.asset.save()
        messages.success(request, 'Asset unassigned successfully')
    return redirect('assets:assigned_list')

def delete_assign_asset_list(request, id):
    if request.method == 'POST':
        asset=Asset.objects.filter(id=id).first()
        asset.is_assigned=False
        set_asset=AssetStatus.objects.filter(Q(organization=request.user.organization) | Q(organization__isnull=True), name='Available').first()
        asset.asset_status=set_asset
        asset.save()
        assignAsset = get_object_or_404(
            AssignAsset, asset=asset, asset__organization=request.user.organization)
        assignAsset.delete()
    return redirect('assets:list')

@login_required
def assign_asset_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'assets/assigned-assets-data.html', {
            'page_object': AssignAsset.objects.filter(Q(asset__organization=request.user.organization) & (Q(
                asset__name__icontains=search_text) | Q(asset__serial_no__icontains=search_text) | Q(user__full_name__icontains=search_text) | Q(user__department__name__icontains=search_text)
            )).order_by('-asset__created_at')[:10]
        })

    asset_list = AssignAsset.objects.filter(
        asset__organization=request.user.organization).order_by('-asset__created_at')
    paginator = Paginator(asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'assets/assigned-assets-data.html', {'page_object': page_object})

@login_required
def change_status(request, id):
    # asset_id=request.GET.get('id')
    if request.method in ['PATCH', 'POST']:
        try:
            asset = Asset.objects.filter(id=id).first()
        except Asset.DoesNotExist:
            return JsonResponse({'error': 'Asset not found'}, status=404)
        try:
            data = json.loads(request.body)
            new_status = (data.get('status'))
        except (ValueError, KeyError, json.JSONDecodeError)as e:
            return HttpResponseBadRequest('Invalid data')

        # if new_status not in dict(Asset.STATUS_CHOICES).keys():
        #     return JsonResponse({'error': 'Invalid status'}, status=400)
        get_status=AssetStatus.objects.filter(Q(organization=request.user.organization) | Q(organization__isnull=True), name=new_status).first()
        asset.asset_status = get_status
        asset.updated_by=request.user.full_name
        if asset.asset_status != "Available":  # If status is 'Assigned'
            asset.is_assigned = False
            # delete the assigned asset from the asigned asset list
            AssignAsset.objects.filter(asset=asset).delete()
        asset.save()
        return JsonResponse({'success': True, 'new_status': new_status})


    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@permission_required('authentication.add_asset_status')
def add_asset_status(request):
    form=AssetStatusForm(request.POST or None, request.user.organization)

    if request.method=="POST":
        if form.is_valid():
            asset_status=form.save(commit=False)
            asset_status.organization=request.user.organization
            asset_status.save()
            messages.success(request, "Status added sucessfully")
            # return redirect('assets:asset_status_list')
        
            # For HTMX: return 204 No Content to indicate success
            if request.headers.get('Hx-Request') == 'true':
                return HttpResponse(status=204)
            
            # For regular requests fallback
            return HttpResponseRedirect(reverse('assets:asset_status_list'))
    context = {'form': form, "modal_title": "Add Asset Status"}  
    return render(request,'assets/add_asset_status.html', context)

@login_required
@user_passes_test(manage_access_for_assets_status)
def asset_status_list(request):
    all_asset_status_list = AssetStatus.undeleted_objects.filter(Q(organization=None)|
    Q(organization=request.user.organization)).order_by('-created_at')

    deleted_asset_status_count= AssetStatus.deleted_objects.filter(Q(organization=None, can_modify=True)|
    Q(organization=request.user.organization, can_modify=True)).count()

    paginator = Paginator(all_asset_status_list,
        PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'admin',
        'submenu': 'Asset_Status',
        'page_object': page_object,
        'deleted_asset_status_count':deleted_asset_status_count,
        'title': 'Asset Status'
    }
    return render(request,'assets/asset_status_list.html',context=context)

@login_required
@permission_required('authentication.asset_status_details')
def asset_status_details(request,id):
    asset_status = get_object_or_404(
    AssetStatus.undeleted_objects, pk=id, organization=request.user.organization)

    history_list = AssetStatus.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {'sidebar': 'admin', 'page_object': page_object,
               'submenu': 'asset_status', 'asset_status': asset_status, 'title': 'Asset_Status - Details'}
    return render(request, 'assets/asset_status_details.html', context=context)

@login_required
@permission_required('authentication.edit_asset_status')
def edit_asset_status(request,id):
    asset_status = get_object_or_404(
    AssetStatus.undeleted_objects, pk=id, organization=request.user.organization)
    form = AssetStatusForm(request.POST or None, instance=asset_status,
                               organization=request.user.organization,  pk=asset_status.id)

    if request.method == "POST":

        if form.is_valid():
            form.save()
            messages.success(request, 'Asset Status updated successfully')
            return HttpResponse(status=204)

    context = {'form': form, "modal_title": "Update Asset Status"}
    return render(request, 'assets/add_asset_status.html', context)

@login_required
def asset_status_search(request, page):
    search_text = request.GET.get('search_text').strip()
    if search_text:
        return render(request, 'assets/asset-status-data.html', {
            'page_object': AssetStatus.undeleted_objects.filter(Q(organization=request.user.organization) & Q(name__icontains=search_text)).order_by('-created_at')[:10]
        })

    status_list = AssetStatus.undeleted_objects.filter(
        organization=request.user.organization).order_by('-created_at')
    paginator = Paginator(status_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = page
    page_object = paginator.get_page(page_number)
    return render(request, 'assets/asset-status-data.html', {'page_object': page_object})


@login_required
@permission_required('authentication.delete_asset_status')
def delete_asset_status(request,id):
    if request.method == 'POST':
        product_category = get_object_or_404(
        AssetStatus.undeleted_objects, pk=id, organization=request.user.organization)
        product_category.status = False
        product_category.soft_delete()
        history_id = product_category.history.first().history_id
        product_category.history.filter(pk=history_id).update(history_type='-')
        messages.success(request, 'Asset Status deleted successfully')

    return redirect(request.META.get('HTTP_REFERER'))

@login_required
@permission_required('authentication.edit_asset')
def update_in_detail(request, id):
    asset = get_object_or_404(Asset, pk=id, organization=request.user.organization)
    asset_images = AssetImage.objects.filter(asset=asset)
    assetSpecifications = AssetSpecification.objects.filter(asset=asset)
    custom_fields = CustomField.objects.filter(entity_type='asset', object_id=asset.id, organization=request.user.organization)
    current_path = request.path
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            delete_ids = data.get('delete_image_ids', [])
            if delete_ids:
                AssetImage.objects.filter(id__in=delete_ids, asset=asset).delete()
                return JsonResponse({'success': True, 'message': 'Images deleted successfully.'})
            else:
                return JsonResponse({'success': False, 'message': 'No image IDs provided.'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)

    elif request.method == 'POST':
        form = AssetForm(request.POST, instance=asset, organization=request.user.organization)
        image_form = AssetImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            form.save()
            assetSpecifications.delete()
            # Handle image removals (if any from POST)
            delete_ids = request.POST.getlist('delete_image_ids')
            if delete_ids:
                AssetImage.objects.filter(id__in=delete_ids, asset=asset).delete()

            # Handle new images
            images = request.FILES.getlist('image')
            for img_file in images:
                AssetImage.objects.create(asset=asset, image=img_file)

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
                            object_id=asset.id,
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
                        object_id=asset.id,
                        field_type='text',
                        field_name=name.strip(),
                        field_value=val.strip(),
                        entity_type='asset',
                        organization=request.user.organization
                    )
                    print("Custom Field added successfully 2")
            # Success message and redirect
            messages.success(request, "Asset updated successfully.")
            return redirect('assets:update_in_detail', id=asset.id)
    else:
        form = AssetForm(instance=asset, organization=request.user.organization)
        image_form = AssetImageForm()

    context = {
        'sidebar': 'assets',
        'submenu': 'list',
        'image_form': image_form,
        'asset_images': asset_images,
        'form': form,
        'asset': asset,
        'assetSpecifications': assetSpecifications,
        'title': 'Asset - Update',
        'custom_fields': custom_fields
    }
    if current_path == f'/assets/update-assets-details/{id}/':
        return render(request, 'assets/update-assets-in-detail.html', context=context)
    elif current_path == f'/assets/update/{id}/':
        return render(request, 'assets/update-assets.html', context=context)


def piechart_status_data(request):
    data = Asset.objects.values('asset_status__name').annotate(total=Count('id'))
    return data
# This gives a list of statuses with counts, which can then be fed to a chart creation library.

def pie_chart_assigned_status(request):
    data = Asset.objects.all()
    assigned=0
    unassigned=0
    for asset in data:
        if asset.is_assigned:
            assigned+= 1
        else:
            unassigned+= 1
    if data is None:
        chart_data = [
          ['Status', 'Assets'],
          ['Assigned', 0],
          ['Unassigned', 0],
        ]
    chart_data=[
          ['Status','Assets'],
          ['Assigned',assigned],
          ['Unassigned',unassigned],
        ]
    return JsonResponse({
        'chart_data': chart_data
    })

def pie_chart_status(request):
    data = Asset.undeleted_objects.values('asset_status__name').annotate(total=Count('id'))
    no_data=None
    if data is None:
        no_data='No Data Found'
    chart_data = [['Status', 'Assets']]
    for item in data:
        chart_data.append([item['asset_status__name'], item['total']])
    filtered_chart_data = [row for row in chart_data if row[0] is not None]
    return JsonResponse({'chart_data': filtered_chart_data,'no_data':no_data})

# [["Status", "Assets"], [null, 2], ["Lost/Stolen", 1], ["Out for Repair", 1], ["Assigned", 3], ["Available", 6]]
def assign_asset_in_asset_list(request, id):
    asset = get_object_or_404(Asset, pk=id, organization=request.user.organization)
    # data = dict(request.POST)
    # if data is not None:
    #     data["asset"] = asset.pk
    form = AssignedAssetListForm(request.POST,
                             organization=request.user.organization)
    image_form = AssetImageForm(request.FILES)
    if request.method == 'POST':
        if form.is_valid() and image_form.is_valid():
            assign_obj = form.save(commit=False)
            assign_obj.asset = asset        # Explicitly set asset!
            assign_obj.save()
            form.save_m2m()
            asset.is_assigned = True
            asset.asset_status = AssetStatus.objects.filter(Q(organization=request.user.organization) | Q(organization__isnull=True), name='Assigned').first()
            asset.save()
            # print("infoooooooooooo",form.data)
            # files=request.FILES.getlist('image')
            # print("FILES",files)
            # img_files=image_form.data('image')
            # print("img_files",img_files)
    
            # print("other IMAGESSSSSSSSSS",img_files)
            files = request.FILES.getlist('images')
            # print("FILES",files)
            for f in files:
                AssetImage.objects.create(asset=asset, image=f)
            messages.success(request, 'Asset assigned to user successfully')
            return HttpResponse(status=204)
        else:
            return redirect('assets:list')
    else:
        form = AssignedAssetListForm(organization=request.user.organization)
        image_form = AssetImageForm()
    context = {'form': form,'image_form':image_form,'asset':asset}
    return render(request, 'assets/assign-asset-modal-in-list.html', context=context)