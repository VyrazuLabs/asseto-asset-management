from django.utils import timezone
from assets.models import Asset, AssetImage, AssignAsset
from dateutil.relativedelta import relativedelta
from dashboard.models import CustomField

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
            asset_dict["assignedTo"] = assigned_asset.user.id if assigned_asset and assigned_asset.user else None
        else:
            asset_dict["assignedTo"] = None

        asset_list.append(asset_dict)

    return asset_list


def asset_data(request,asset,asset_images,asset_barcode,asset_statuses):
    current_host=request.get_host()
    asset_data={
        "id":asset.id,
        "tag":asset.tag,
        "name":asset.name,
        "product":asset.product.name,
        "product type":asset.product.product_type.name,
        "product_category":asset.product.product_category.name if asset.product.product_category else None,
        "serial no.":asset.serial_no if asset.serial_no else None,
        "price":asset.price if asset.price else None,
        "office_location":asset.location.office_name if asset.location else None,
        "purchase type":asset.purchase_type if asset.purchase_type else None,
        "purchase_date":asset.purchase_date if asset.purchase_date else None,
        "warranty_expiry_date":asset.warranty_expiry_date if asset.warranty_expiry_date else None,
        "vendor":asset.vendor.name if asset.vendor else None,
        "asset_status":asset.asset_status.name if asset.asset_status else None,
        "serial_no":asset.serial_no if asset.serial_no else None,
        "description":asset.description if asset.description else None,
        "barcode":asset_barcode
    }
    asset_image_list=[]
    for images in asset_images:
        add_path=f"http://{current_host}"+images.image.url
        asset_image_list.append(add_path)
    asset_data['asset_images']=asset_image_list

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
    if not asset:
        raise ValueError("Asset with this tag does not exists!")
 
    return {"asset_id": asset.id}
