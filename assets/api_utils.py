from django.utils import timezone
from datetime import datetime, timedelta
from assets.models import Asset, AssetImage, AssignAsset,AssetStatus
from dateutil.relativedelta import relativedelta
import re
from django.db.models import F
from authentication.models import User
from common.API_custom_response import api_response
from django.shortcuts import get_object_or_404
from datetime import date
from configurations.utils import get_currency_and_datetime_format, format_datetime
from configurations.utils import dynamic_display_name
from django.db.models import Func, CharField
from dashboard.models import CustomField
from notifications.models import UserNotification
# from assets.api_utils import BaseSegmentFunc

def assign_asset_user_list(request):
    get_users=User.undeleted_objects.filter(status=True, organization=request.user.organization).exclude(pk=request.user.id)
    data=[{'id':user.id,'name':user.full_name} for user in get_users]
    return data


def asset_details(id,request):
    asset=get_object_or_404(Asset,pk=id)
    asset_images=AssetImage.objects.filter(asset=asset).all()
    custom_fields=CustomField.objects.filter(object_id=asset.id)
    asset_statuses=AssetStatus.objects.all()
    data=asset_data(request,asset,asset_images,asset_statuses,custom_fields)
    return data

def mark_notification_as_seen(notification_id, request):
    notification = get_object_or_404(
                UserNotification,
                id=notification_id,
                user=request.user
            )

    notification.is_seen = True
    notification.save(update_fields=["is_seen"])
def get_notification_data(request):
    notifications= UserNotification.objects.filter(
                    user=request.user,
                    is_seen=False,
                    notification__entity_type=0
                ).annotate(
                    object_type=BaseSegmentFunc('notification__link'),
                    notification_title=F('notification__notification_title'),
                    notification_text=F('notification__notification_text'),
                    link=F('notification__link'),
                    created_at=F('notification__created_at'),
                    object_id=F('notification__object_id')
                ).order_by('-notification__created_at')
    data = notifications.values(
        'id', 
        'notification_title',
        'notification_text',
        'is_seen', 
        'link',
        'object_type',
        'created_at', 
        'object_id'
    )
    return data
# def get_push_notification_data(user):
#     return {
#         "message": "Success",
#         "user": user.username
#     }
class BaseSegmentFunc(Func):
    output_field = CharField()

    template = """
        CASE 
            WHEN %(expressions)s IS NOT NULL AND %(expressions)s != ''
            THEN SUBSTRING_INDEX(
                    SUBSTRING_INDEX(%(expressions)s, '/', 2),
                    '/',
                    -1
                 )
            ELSE NULL
        END
    """
def get_base_segment(path: str):
    if not path:
        return None
    return next((segment for segment in path.split("/") if segment), None)
def convert_to_list(request,queryset):
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
        user=request.user
        if asset.is_assigned:
            assigned_asset = AssignAsset.objects.filter(asset=asset.id).select_related("user").first()
            asset_dict["assigned_to_name"] = dynamic_display_name(request,fullname=assigned_asset.user.full_name) if assigned_asset and assigned_asset.user else None,
            asset_dict["assigned_to_image"] = f"http://{current_host}"+assigned_asset.user.profile_pic.url if assigned_asset and assigned_asset.user and assigned_asset.user.profile_pic else None
        else:
            asset_dict["assigned_to_name"] = None
            asset_dict["assigned_to_image"] = None

        asset_list.append(asset_dict)
    return asset_list

# dynamic_display_name(user.full_name)
def get_assigned_user(request,asset):
    user=request.user
    assigned_user=None
    if asset.is_assigned:
        assigned_asset=AssignAsset.objects.filter(asset=asset).select_related("user").first()
        if assigned_asset:
            assigned_user={
                "id":assigned_asset.user.id,
                "full_name":dynamic_display_name(request,fullname=assigned_asset.user.full_name) if assigned_asset and assigned_asset.user else None,
                "email":assigned_asset.user.email
            }
    return assigned_user
def asset_data(request,asset,asset_images,asset_statuses,custom_fields):
    current_host=request.get_host()
    obj=get_currency_and_datetime_format(request.user.organization)
    format_currency=obj['currency'] if obj['currency'] else 'INR'
    format_date=obj['date_format'] if obj['date_format'] else None
    # formatted_currency= format_currency.format(asset.price) if asset.price else None
    assign_info=None
    if asset.is_assigned is True:
        assign_info=get_assigned_user(request,asset)
    asset_data={
        "id":asset.id,
        "tag":asset.tag,
        "assigned_status":asset.is_assigned,
        "name":asset.name,
        "product_id":asset.product.id,
        "product":asset.product.name, 
        "product_type":asset.product.product_type.name,
        "product_category":asset.product.product_sub_category.name if asset.product.product_sub_category else None,
        "serial_no":asset.serial_no if asset.serial_no else None,
        "price":format_currency+" "+str(asset.price) if asset.price else None,#asset.price if asset.price else None,
        "office_location_id":asset.location.id if asset.location else None,
        "office_location":asset.location.office_name if asset.location else None,
        "purchase_type":asset.purchase_type if asset.purchase_type else None,
        "purchase_date":format_datetime(asset.purchase_date,format_date) if asset.purchase_date else None,
        "original_purchase_date":datetime.strptime(str(asset.purchase_date), "%Y-%m-%d").isoformat() if asset.purchase_date else None,
        # datetime.strptime(str(asset.warranty_expiry_date), "%Y-%m-%d").isoformat()
        "warranty_expiry_date":format_datetime(asset.warranty_expiry_date,format_date) if asset.warranty_expiry_date else None,
        "original_warranty_expiry_date":datetime.strptime(str(asset.warranty_expiry_date), "%Y-%m-%d").isoformat() if asset.warranty_expiry_date else None,
        "vendor_id":asset.vendor.id if asset.vendor else None,
        "vendor":asset.vendor.name if asset.vendor else None,
        "asset_status_id":asset.asset_status.id if asset.asset_status else None,
        "asset_status":asset.asset_status.name if asset.asset_status else None,
        "serial_no":asset.serial_no if asset.serial_no else None,
        "description":asset.description if asset.description else None,
        "is_assigned":asset.is_assigned if asset.is_assigned else None,
        "assigned_to":assign_info["full_name"] if assign_info else None,
        "assigned_to_id":assign_info["id"] if assign_info else None,
        "date_format":format_date if format_date else None,
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

    # asset_status_list=[]
    # for asset_status in asset_statuses:
    #     asset_status_dict={
    #         'id':asset_status.id,
    #         'name':asset_status.name
    #     }
    #     asset_status_list.append(asset_status_dict)
    
    # asset_data['asset_statuses']=asset_status_list

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
    if not asset:
        raise ValueError("Asset with this tag does not exists!")
 
    return {"asset_id": asset.id,"assigned_to_id":get_assign_asset.id,"assigned_to_name":get_assign_asset.user.full_name} if get_assign_asset else {"asset_id": asset.id,"assigned_to_id":None,"assigned_to_name":None}

def delete_images(deleted_image_ids):
    for id in deleted_image_ids:
        try:
            AssetImage.objects.filter(id=id).delete()
        except Exception as e:
            print("exception",e)

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