import json
import os
from django.http import JsonResponse
from django.utils import timezone
from audit.models import Audit, AuditImage
from configurations.models import TagConfiguration
from configurations.utils import dynamic_display_name, format_datetime, generate_asset_tag, get_currency_and_datetime_format
from .models import Asset,AssignAsset,AssetImage,AssetStatus,Location,Vendor
from dashboard.models import CustomField, Department,ProductType,ProductCategory
from .forms import AssetForm, AssignedAssetForm,ReassignedAssetForm
from django.core.paginator import Paginator
from django.db.models import Q,Prefetch
from .models import Asset
from configurations.models import SlackConfiguration
from django.http import JsonResponse, HttpResponse
from datetime import date,datetime
from dateutil.relativedelta import relativedelta
import requests

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

PAGE_SIZE = 10
ORPHANS = 1

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
    asset_ids_in_page = [asset.id for asset in page_object]
    images_qs = AssetImage.objects.filter(asset_id__in=asset_ids_in_page).order_by('-uploaded_at')
    
    # Map asset ID to its first image
    asset_images = {}
    for img in images_qs:
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img
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


def filtered_asset(request):
    user_data=request.POST.get("user-data")
    product=request.POST.get("product")# gets the id of the product
    search_text = (request.GET.get("search_text") or "").strip()
    vendor_id = request.GET.get("vendor")
    status_id = request.POST.get("status")
    department_id = request.POST.get("department")
    location_id = request.POST.get("location")
    category_id = request.POST.get("category")
    type_id = request.POST.get("type")

    filters = Q(organization=request.user.organization)
    if search_text:
        filters &= (
            Q(tag__icontains=search_text) |
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
        filters &= Q(vendor_id=vendor_id)
    if status_id:
        filters &= Q(asset_status_id=status_id)
    if category_id:
        filters &= Q(product__product_sub_category_id=category_id)
    if type_id:
        filters &= Q(product__product_type_id=type_id)
    if location_id:
        filters &= Q(location_id=location_id)

    assets_qs = Asset.undeleted_objects.filter(filters).order_by("-created_at")
    #Filter by product based on product type and category
    if product:
        assets_qs=assets_qs.filter(product_id=product)
    if user_data:
        assigned_qs = AssignAsset.objects.filter(user_id=user_data).select_related("user").order_by("-assigned_date")
        assets_qs = (
            assets_qs.filter(assignasset__user=user_data)
            .prefetch_related(Prefetch("assignasset_set", queryset=assigned_qs, to_attr="assignments"))
        )
    if department_id:
        assigned_qs = AssignAsset.objects.filter(user__department_id=department_id)
        assets_qs = assets_qs.filter(assignasset__user__department_id=department_id)
    
    return assets_qs

def create_asset_list(request,assets_qs):
    list_of_audits=Audit.objects.all()
    list_of_assigned_audits=[audit.asset.id for audit in list_of_audits ]
    list_of_audited_assets=Asset.objects.filter(id__in=list_of_assigned_audits)
    product_category_list=ProductCategory.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization))
    department_list=Department.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization))
    location_list=Location.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization))
    user_list=User.objects.filter(Q(organization=None) | Q(organization=request.user.organization),is_active=True).order_by('-created_at')
    vendor_list=Vendor.objects.filter(Q(organization=None) | Q(organization=request.user.organization)).order_by('-created_at')
    asset_status_list=AssetStatus.objects.filter(Q(organization=None) | Q(organization=request.user.organization))
    product_type_list=ProductType.objects.filter(Q(organization=None) | Q(organization=request.user.organization)).order_by('-created_at')
    asset_list = Asset.undeleted_objects.filter(Q(organization=None) | Q(organization=request.user.organization)).order_by('-created_at')
    deleted_asset_count=Asset.deleted_objects.count()
    get_assigned_asset_list=AssignAsset.objects.filter(Q(asset__in=asset_list) & Q(asset__organization=None) | Q(asset__organization=request.user.organization)).order_by('-assigned_date')
    asset_user_map = {}
    for assign in get_assigned_asset_list:
        if assign.asset_id not in asset_user_map:
            asset_user_map[assign.asset_id] = None
        if assign.user:  # avoid None users
            asset_user_map[assign.asset_id]={"full_name":dynamic_display_name(request,fullname=assign.user.full_name),"image":assign.user.profile_pic}
    paginator = Paginator(asset_list, PAGE_SIZE, orphans=ORPHANS)
    if assets_qs.exists():
        paginator = Paginator(assets_qs, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    asset_form = AssetForm(organization=request.user.organization)
    assign_asset_form = AssignedAssetForm(organization=request.user.organization)
    reassign_asset_form = ReassignedAssetForm(organization=request.user.organization)
    active_users=User.objects.filter(is_active=True,organization=request.user.organization)
    # Gather the first image per asset in the current page
    asset_ids_in_page = [asset.id for asset in page_object]
    images_qs = AssetImage.objects.filter(asset_id__in=asset_ids_in_page).order_by('-uploaded_at')
    is_demo=os.environ.get('IS_DEMO')
    if is_demo:
        is_demo=True
    else:
        is_demo=False
    # Map asset ID to its first image
    asset_images = {}
    for img in images_qs:
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img
    context = {
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
        'title': 'Assets',
        'is_demo':is_demo,
        'list_of_audited_assets':list_of_audited_assets
    }
    return context

def asset_details(request,get_audit_history,get_audit_image,asset,assiggned_asset,assetSpecifications,get_asset_img,asset_barcode):
    audit_data = []
    if get_audit_history:
        for audit in get_audit_history:
            data = {
                "id": audit.id,
                "asset_name": audit.asset.name,
                "condition_label": audit.condition_label,
                "notes": audit.notes,
                "created_at": audit.created_at,
                "audit_image": AuditImage.objects.filter(audit=audit).order_by('-uploaded_at').first()
            }
            audit_data.append(data)
    
    if assiggned_asset and assiggned_asset.user:
        assigned_user=assiggned_asset.user.full_name
    else:
        assigned_user=None
    
    if asset is None:
        assetSpecifications=AssignAsset.objects.filter(id=id).first()
        asset=assetSpecifications.asset

    
    img_array=[]
    
    for it in get_asset_img:
        img_array.append(it)
    months_int=asset.product.eol
    today=timezone.now().date()
    if months_int: 
        eol_date= today+relativedelta(months=months_int)
    else:
        eol_date=None
    arr_size=len(img_array)
    history_list = asset.history.all()
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    get_custom_data=[]
    get_data=CustomField.objects.filter(object_id=asset.id)
    organization=request.user.organization
    obj=get_currency_and_datetime_format(organization)
    get_currency=obj['currency']
    get_date_format=obj['date_format']
    is_demo=True
    if is_demo:
        is_demo=True
    else:
        is_demo=False
    if get_date_format:
        asset.warranty_expiry_date = format_datetime(x=asset.warranty_expiry_date, output_format=get_date_format) if asset.warranty_expiry_date is not None else ""
        asset.purchase_date = format_datetime(x=asset.purchase_date, output_format=get_date_format) if asset.purchase_date is not None else ""
        eol_date=format_datetime(x=eol_date, output_format=get_date_format) if eol_date is not None else ""
    for it in get_data:
        obj={}
        obj['field_name']=it.field_name
        obj['field_value']=it.field_value
        get_custom_data.append(obj)

    context = {'sidebar': 'assets', 'assigned_user':assigned_user,'asset_barcode':asset_barcode,'asset': asset, 'submenu': 'list', 'page_object': page_object,'arr_size':arr_size,
               'assetSpecifications': assetSpecifications, 'title': f'Details-{asset.tag}-{asset.name}','get_asset_img':img_array,'eol_date':eol_date,'get_custom_data':get_custom_data,'get_currency':get_currency,'is_demo':is_demo,'get_audit_history':audit_data,'get_audit_image':get_audit_image}

    return context

def search_with_filters(request,list_of_audited_assets):
    search_text = (request.GET.get('search_text') or "").strip()
    vendor_id = request.GET.get('vendor')
    status_id = request.GET.get('status')
    user_id = request.GET.get('user')
    department_id=request.GET.get('department')
    product_category_id = request.GET.get('category')
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
            Q(product__product_type__name__icontains=search_text)|
            Q(tag__icontains=search_text)
        )

    if vendor_id:
        q &= Q(vendor_id=vendor_id)

    if status_id:
        q &= Q(asset_status_id=status_id)
    
    if product_category_id:
        q &= Q(product__product_category__id=product_category_id)
    
    if product_type_id:
        q &= Q(product__product_type_id=product_type_id)

    page_object = list(Asset.undeleted_objects.filter(q).order_by('-created_at')[:10])

    asset_ids = [obj.id for obj in page_object]
    image_object = AssetImage.objects.filter(
        asset__organization=request.user.organization,
        asset_id__in=asset_ids
    ).order_by('-uploaded_at')

    asset_images = {}
    for img in image_object:
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img

    if user_id:
        assigned_qs = AssignAsset.objects.filter(user_id=user_id).select_related("user").order_by("-assigned_date")
        page_object = (
            Asset.undeleted_objects
            .filter(q, assignasset__user_id=user_id)
            .prefetch_related(Prefetch("assignasset_set", queryset=assigned_qs, to_attr="assignments"))
            .order_by("-created_at")[:10]
        )
    elif department_id: 
        assigned_qs = AssignAsset.objects.filter(user__department_id=department_id)
        page_object = (
            Asset.undeleted_objects
            .filter(q, assignasset__user__department_id=department_id)
            .order_by("-created_at")[:10]
        )
    else:
        page_object = Asset.undeleted_objects.filter(q).order_by("-created_at")[:10]

    asset_user_map = {}
    get_assigned_asset_list = AssignAsset.objects.filter(
        asset_id__in=asset_ids,
        asset__organization=request.user.organization
    ).order_by('-assigned_date')
    for assign in get_assigned_asset_list:
        if assign.asset_id not in asset_user_map:
            asset_user_map[assign.asset_id] = None
        if assign.user:  # avoid None users
            asset_user_map[assign.asset_id]={"full_name":dynamic_display_name(request,fullname=assign.user.full_name),"image":assign.user.profile_pic}
    
    context={
            'page_object': page_object,
            'asset_user_map': asset_user_map,
            'asset_images': asset_images,
            'list_of_audited_assets':list_of_audited_assets
        }
    return context

def create_custom_fileds(request,asset):
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
            
def autogenerated_tag(request,form):
        tag_config=TagConfiguration.objects.filter(organization=request.user.organization,use_default_settings=True).first()
        if tag_config:
            form.data['tag'] = generate_asset_tag(prefix=tag_config.prefix, number_suffix=tag_config.number_suffix)
        else:
            form.data['tag'] = generate_asset_tag(prefix='VY', number_suffix='001')

def create_char_data(data):
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
    return chart_data


def delete_asset_images(request, asset):
    try:
        data = json.loads(request.body)
        delete_ids = data.get('delete_image_ids', [])

        if not delete_ids:
            return JsonResponse({'success': False, 'message': 'No image IDs provided.'}, status=400)

        AssetImage.objects.filter(id__in=delete_ids, asset=asset).delete()
        return JsonResponse({'success': True, 'message': 'Images deleted successfully.'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)


def save_new_images(request, asset):
    for img in request.FILES.getlist('image'):
        AssetImage.objects.create(asset=asset, image=img)


def update_existing_custom_fields(request, custom_fields):
    for cf in custom_fields:
        key = f"custom_field_{cf.entity_id}"
        new_value = request.POST.get(key, "")

        if new_value != cf.field_value:
            cf.field_value = new_value
            cf.save()

#Previous Workflow
# def slack_notification(request,text,object,tag):
#     redirect_url=redirect_from_slack_url(request,object)
#     SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

#     now = datetime.now()
#     formatted = now.strftime("%B %d, %Y, %-I:%M %p")
#     link_text = f"<{redirect_url}|{text}>"
#     message = {
#         "text": f"{formatted}: Asset {tag} {link_text}",
#         # Optionally: "channel": "#your-channel", "username": "Notifier"
#     }
#     response = requests.post(SLACK_WEBHOOK_URL, json=message)
#     if response.status_code == 200:         
#         return HttpResponse("Notification sent!", status=200)
#     else:
#         return HttpResponse("Failed to send notification", status=500)

def redirect_from_slack_url(request,obj_id):
    endpoint=f'/assets/details/{obj_id}'
    url=request.build_absolute_uri(endpoint)
    return url

def set_slack_webhook(organization, admin, url):
    obj, created = SlackConfiguration.objects.update_or_create(
        organization=organization,
        admin=admin,
        defaults={'webhook_url': url},
    )

def get_slack_webhook_url(organization, admin):
    try:
        return SlackConfiguration.objects.get(organization=organization, admin=admin).webhook_url
    except SlackConfiguration.DoesNotExist:
        return None

def send_slack_notification(organization, admin, message):
    webhook_url = get_slack_webhook_url(organization, admin)
    if webhook_url:
        import requests
        payload = {"text": message}
        resp = requests.post(webhook_url, json=payload)
        resp.raise_for_status()
        return True
    else:
        # Handle: webhook not set
        return False

#New Integrations
SLACK_API_BASE = "https://slack.com/api"

def headers(token):
    return {"Authorization": f"Bearer {token}"}

# def create_channel_if_not_exists(workspace: SlackWorkspace, channel_name: str, is_private=True):
#     """
#     Ensure a channel exists in the workspace; return channel_id.
#     """
#     token = workspace.bot_access_token
#     # Try to create
#     resp = requests.post(f"{SLACK_API_BASE}/conversations.create", headers=headers(token), data={
#         "name": channel_name,
#         "is_private": "true" if is_private else "false"
#     }).json()

#     if resp.get("ok"):
#         return resp["channel"]["id"]

#     # if name_taken, list and find it
#     err = resp.get("error", "")
#     if err == "name_taken" or "already_in_channel" in err:
#         lst = requests.get(f"{SLACK_API_BASE}/conversations.list", headers=headers(token), params={"limit": 1000}).json()
#         for ch in lst.get("channels", []):
#             if ch.get("name") == channel_name:
#                 return ch.get("id")
#     # else raise/log
#     raise Exception(f"Failed to ensure channel {channel_name}: {resp}")


# def invite_user_by_email(workspace: SlackWorkspace, user_email: str, channel_id: str):
#     token = workspace.bot_access_token
#     # lookup user
#     resp = requests.get(f"{SLACK_API_BASE}/users.lookupByEmail", headers=headers(token), params={"email": user_email}).json()
#     if not resp.get("ok"):
#         # can't find user; may need workspace admin to invite manually
#         return {"ok": False, "error": resp.get("error")}
#     slack_user_id = resp["user"]["id"]

#     invite = requests.post(f"{SLACK_API_BASE}/conversations.invite", headers=headers(token), data={
#         "channel": channel_id,
#         "users": slack_user_id
#     }).json()
#     return invite


#New Integrations with slack bot
def slack_notification(request,text,object,tag):    
    user=request.user
    get_obj=SlackConfiguration.objects.filter(user=user).first()
    bot_token=None
    channel_id=None
    if get_obj is not None:
        bot_token=get_obj.access_token
        channel_id=get_obj.channel_id
    else:
        return HttpResponse("Slack not configured for user", status=400)
    now = datetime.now()
    redirect_url=redirect_from_slack_url(request,object)
    formatted = now.strftime("%B %d, %Y, %-I:%M %p")
    
    link_text = f"<{redirect_url}|{text}>"
    message = f"{formatted}: Asset {tag} {link_text}"
                                                        # Optionally: "channel": "#your-channel", "username": "Notifier"
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {bot_token}"}
    payload = {
        "channel": channel_id,  # channel_id, not name!
        "text": message
    }
    response = requests.post(url, headers=headers, json=payload)
    # return resp.json()
    if response.status_code == 200:
        return HttpResponse("Notification sent!", status=200)
    else:
        return HttpResponse("Failed to send notification", status=500)

#Make a new slack channelfrom scratch.
def create_slack_channel(bot_token, channel_name):
    url = "https://slack.com/api/conversations.create"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": channel_name  # channel names must be lowercase and without spaces
    }
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    if data.get("ok"):
        channel_id = data["channel"]["id"]
        return channel_id
    else:
        return None

def redirect_from_slack_url(request,obj_id):
    endpoint=f'/assets/details/{obj_id}'
    url=request.build_absolute_uri(endpoint)
    return url

def get_host(request):
    endpoint=f'/assets/list'
    host=request.build_absolute_uri(endpoint)
    return host

# def generate_asset_tag(prefix='VY', start=1, size=4):
#     """
#     Generate an auto-incrementing tag with given prefix and fixed size for number part.
#     Example: prefix='VY', size=4 -> VY0001, VY0002, ...
#     """
#     from assets.models import Asset

#     # Get last asset tag that starts with prefix
#     last_tag = Asset.objects.filter(tag__startswith=prefix).order_by('-created_at').first()
#     if last_tag and last_tag.tag[len(prefix):].isdigit():
#         last_num = int(last_tag.tag[len(prefix):])
#         next_num = last_num + 1
#     else:
#         next_num = start

#     # Format number with leading zeros according to size
#     number_str = str(next_num).zfill(size)

#     return f"{prefix}{number_str}"