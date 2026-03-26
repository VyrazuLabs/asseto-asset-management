from assets.models import Asset, AssignAsset, AssetImage
from dashboard.models import CustomField
from products.models import ProductImage,Product
from django.db.models import Q,Count
from authentication.models import User
from users.utils import user_data

def convert_product_to_list(request,products):
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

def convert_asset_to_list(request,queryset):
    current_host=request.get_host()
    asset_list = []
    for asset in queryset:
        asset_dict = {
            'id': asset.id,
            'name': asset.name,
            'tag': asset.tag if asset.tag else None,
            "vendor_name": asset.vendor.name if asset.vendor else None,
            "vendor_id": asset.vendor.id if asset.vendor else None,
            'product_id':asset.product.id if asset.product else None,
            'product_name':asset.product.name if asset.product else None,
            'product_type_id':asset.product.product_type.id if asset.product and asset.product.product_type else None,
            'product_type':asset.product.product_type.name if asset.product and asset.product.product_type else None,
            "is_assigned": asset.is_assigned,
            "asset_status": asset.asset_status.name if asset.asset_status else None,
            "asset_status_id": asset.asset_status.id if asset.asset_status else None,
        }
        assetImage=AssetImage.objects.filter(asset=asset.id).first()
        asset_dict["image"]=f"http://{current_host}"+assetImage.image.url if assetImage else None
        if asset.is_assigned:
            assigned_asset = AssignAsset.objects.filter(asset=asset.id).select_related("user").first()
            asset_dict["assigned_to_name"] = assigned_asset.user.full_name if assigned_asset and assigned_asset.user else None
            asset_dict["assigned_to_image"] = f"http://{current_host}"+assigned_asset.user.profile_pic.url if assigned_asset and assigned_asset.user and assigned_asset.user.profile_pic else None
        else:
            asset_dict["assigned_to_name"] = None
            asset_dict["assigned_to_image"] = None

        asset_list.append(asset_dict)

    return asset_list

def search_utils(request,search_text):
    org_filter = Q(organization=request.user.organization) | Q(organization=None)
    response_data = {
        "products": [],
        "assets": [],
        "users": []
    }

    # -------- Products --------
    products = Product.undeleted_objects.filter(
        org_filter & Q(name__icontains=search_text)
    ).annotate(
        total_assets=Count('asset'),
        available_assets=Count('asset', filter=Q(asset__is_assigned=False))
    ).order_by('-created_at')[:10]

    if products.exists():
        response_data["products"] = convert_product_to_list(request, products)

    # -------- Assets --------
    assets = Asset.undeleted_objects.filter(
        org_filter & (
            Q(tag__icontains=search_text) |
            Q(name__icontains=search_text)
        )
    ).order_by('-created_at')[:10]

    if assets.exists():
        response_data["assets"] = convert_asset_to_list(request, assets)

    # -------- Users (Superuser only) --------
    if request.user.is_superuser:
        users = User.undeleted_objects.filter(
            org_filter &
            Q(is_superuser=False) &
            Q(full_name__icontains=search_text)
        ).exclude(pk=request.user.id).order_by('-created_at')[:10]

        if users.exists():
            response_data["users"] = user_data(request, users)

    return response_data