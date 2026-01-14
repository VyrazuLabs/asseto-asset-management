from assets.models import Asset, AssignAsset, AssetImage
from dashboard.models import CustomField
from products.models import ProductImage

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
        print("pro------->",product_dict)
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
            "vendorName": asset.vendor.name if asset.vendor else None,
            "vendorId": asset.vendor.id if asset.vendor else None,
            'productId':asset.product.id if asset.product else None,
            'productName':asset.product.name if asset.product else None,
            'product_type_id':asset.product.product_type.id if asset.product and asset.product.product_type else None,
            'product_type':asset.product.product_type.name if asset.product and asset.product.product_type else None,
            "isAssigned": asset.is_assigned,
            "assetStatus": asset.asset_status.name if asset.asset_status else None,
            "assetStatusId": asset.asset_status.id if asset.asset_status else None,
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