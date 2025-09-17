from .models import Asset, AssetSpecification, AssignAsset,AssetImage,AssetStatus,Location,Vendor
from dashboard.models import Department,ProductType,ProductCategory
from .forms import AssetForm, AssignedAssetForm,AssignedAssetListForm, ReassignedAssetForm,AssetImageForm,AssetStatusForm
from django.core.paginator import Paginator
from django.db.models import Q,Prefetch

PAGE_SIZE = 10
ORPHANS = 1
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
def release_asset(request, asset_id):
    if request.method == 'POST':
        asset = get_object_or_404(Asset, pk=asset_id)
        # Assumes status 3 means "Ready To Deploy"
        asset.status = 3
        asset.save()
        messages.success(request, f"Asset '{asset.name}' has been released and is now Ready To Deploy.")
    return redirect('assets:list')

from django.contrib.auth import get_user_model

@login_required
@permission_required('assets.change_asset', raise_exception=True)
def assign_asset(request, asset_id):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        asset = get_object_or_404(Asset, pk=asset_id)
        # Assumes you have a field like asset.assigned_user (ManyToOne/User FK)
        # User = get_user_model()
        selected_user = get_object_or_404(User, pk=user_id, is_active=True)
        asset.assigned_user = selected_user
        get_assigned_asset=AssignAsset.objects.filter(asset=asset).first()
        if get_assigned_asset is not None:
            asset.status = 0  # Example: 0 for "Assigned"
        asset.save()
        messages.success(request, f"Asset '{asset.name}' assigned to {selected_user.get_full_name() or selected_user.username}.")
    return redirect('assets:list')

def get_asset_filter_data(request):
    product_category_list=ProductCategory.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization))
    department_list=Department.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization))
    location_list=Location.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization))
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
            asset_user_map[assign.asset_id]={"full_name":assign.user.full_name,"image":assign.user.profile_pic}
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
    print("MAPPEDDDDDDDDDD",asset_user_map)
    return {
        'product_category_list':product_category_list,
        'department_list':department_list,
        'location_list':location_list,
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