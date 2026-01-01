from django.utils import timezone
from assets.models import Asset, AssetImage, AssignAsset
from dateutil.relativedelta import relativedelta
import re

def convert_to_list(request,queryset):
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

def get_assigned_user(asset):
    assigned_user=None
    if asset.is_assigned:
        assigned_asset=AssignAsset.objects.filter(asset=asset).select_related("user").first()
        if assigned_asset:
            assigned_user={
                "id":assigned_asset.user.id,
                "full_name":assigned_asset.user.full_name,
                "email":assigned_asset.user.email
            }
    return assigned_user
def asset_data(request,asset,asset_images,asset_statuses,custom_fields):
    current_host=request.get_host()
    assign_info=None
    if asset.is_assigned is True:
        assign_info=get_assigned_user(asset)
    asset_data={
        "id":asset.id,
        "tag":asset.tag,
        "assigned_status":asset.is_assigned,
        "name":asset.name,
        "product_id":asset.product.id,
        "product":asset.product.name,
        "product type":asset.product.product_type.name,
        "product_category":asset.product.product_sub_category.name if asset.product.product_sub_category else None,
        "serial no.":asset.serial_no if asset.serial_no else None,
        "price":asset.price if asset.price else None,
        "office_location_id":asset.location.id if asset.location else None,
        "office_location":asset.location.office_name if asset.location else None,
        "purchase type":asset.purchase_type if asset.purchase_type else None,
        "purchase_date":asset.purchase_date if asset.purchase_date else None,
        "warranty_expiry_date":asset.warranty_expiry_date if asset.warranty_expiry_date else None,
        "vendor_id":asset.vendor.id if asset.vendor else None,
        "vendor":asset.vendor.name if asset.vendor else None,
        "asset_status_id":asset.asset_status.id,
        "asset_status":asset.asset_status.name if asset.asset_status else None,
        "serial_no":asset.serial_no if asset.serial_no else None,
        "description":asset.description if asset.description else None,
        "is_assigned":asset.is_assigned if asset.is_assigned else None,
        "assigned_to":assign_info["full_name"] if assign_info else None,
        "assigned_to_id":assign_info["id"] if assign_info else None,
    }
    asset_image_list=[]
    if asset_images:
        for image in asset_images:
            asset_images_dict={'image_id':image.id,'image_path':f"http://{current_host}"+image.image.url}
            asset_image_list.append(asset_images_dict)
    asset_data['asset_images']=asset_image_list

    custom_fields_list=[]
    if custom_fields:
        for custom_field in custom_fields:
            custom_fields_dict={custom_field.field_name:custom_field.field_value}
            custom_fields_list.append(custom_fields_dict)
    asset_data['custom_fields']=custom_fields_list

    months_int=asset.product.eol if asset.product and asset.product.eol else None
    today=timezone.now().date()
    eol_date=None
    if months_int:
        eol_date= today+relativedelta(months=months_int)

    asset_data['eol']=eol_date

    asset_status_list=[]
    for asset_status in asset_statuses:
        asset_status_dict={
            'id':asset_status.id,
            'name':asset_status.name
        }
        asset_status_list.append(asset_status_dict)
    
    asset_data['asset_statuses']=asset_status_list

    return asset_data


def get_asset_id(tag_id):
    get_tag=Asset.objects.filter(tag=tag_id).exists()
    if get_tag:
        asset_id=Asset.objects.get(tag=tag_id)
        respones_data={
            'id':asset_id.id,
            "status": "success"
        }

    else:
        respones_data={
            'status':False,
            'message':"asset with this tag does not exists!"
        }

    return respones_data

def get_asset(tag_id):
    asset=Asset.objects.filter(tag=tag_id).first()
    get_assign_asset=AssignAsset.objects.filter(asset=asset).first() if asset else None
    print("asset",asset)
    if not asset:
        raise ValueError("Asset with this tag does not exists!")
 
    return {"asset_id": asset.id,"assigned_to_id":get_assign_asset.id,"assigned_to_name":get_assign_asset.user.full_name} if get_assign_asset else {"asset_id": asset.id,"assigned_to_id":None,"assigned_to_name":None}

def delete_images(deleted_image_ids):
    for id in deleted_image_ids:
        try:
            AssetImage.objects.filter(id=id).delete()
        except Exception as e:
            print(e)

MM_TO_PX = 3.7795275591  # 96 dpi standard

def mm_to_px(value):
    """Convert `12.34mm` → float(px)."""
    return float(value.replace("mm", "")) * MM_TO_PX

def convert_svg_mm_to_px(svg):
    # Convert <svg width="XXmm" height="XXmm">
    svg = re.sub(
        r'width="([\d\.]+)mm"',
        lambda m: f'width="{mm_to_px(m.group(1))}px"',
        svg
    )
    svg = re.sub(
        r'height="([\d\.]+)mm"',
        lambda m: f'height="{mm_to_px(m.group(1))}px"',
        svg
    )

    # Convert all <rect> x, y, width, height
    svg = re.sub(
        r'(x|y|width|height)="([\d\.]+)mm"',
        lambda m: f'{m.group(1)}="{mm_to_px(m.group(2))}px"',
        svg
    )

    return svg