from .models import Asset, AssetSpecification, AssignAsset,AssetImage,AssetStatus,Location,Vendor,SlackWebhook
from dashboard.models import Department,ProductType,ProductCategory
from .forms import AssetForm, AssignedAssetForm,AssignedAssetListForm, ReassignedAssetForm,AssetImageForm,AssetStatusForm
from django.core.paginator import Paginator
from django.db.models import Q,Prefetch
import requests
from django.http import HttpResponse
from datetime import datetime
from itertools import zip_longest
from .models import Asset,AssignAsset
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from authentication.models import User
import os
<<<<<<< HEAD
=======

>>>>>>> 79fa78fa72d1913ae87d1a5c770f42762a4271ef

PAGE_SIZE = 10
ORPHANS = 1
def grouper(iterable, n):
    # Groups iterable into chunks of size n
    args = [iter(iterable)] * n
    return list(zip_longest(*args, fillvalue=None))


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
    # active_user=[active_users]
    # Gather the first image per asset in the current page
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
<<<<<<< HEAD
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
#         print("Notification sent!")
#         return HttpResponse("Notification sent!", status=200)
#     else:
#         print("Failed:", response.text)
#         return HttpResponse("Failed to send notification", status=500)

def redirect_from_slack_url(request,obj_id):
    endpoint=f'/assets/details/{obj_id}'
    url=request.build_absolute_uri(endpoint)
    return url

def set_slack_webhook(organization, admin, url):
    obj, created = SlackWebhook.objects.update_or_create(
        organization=organization,
        admin=admin,
        defaults={'webhook_url': url},
    )

def get_slack_webhook_url(organization, admin):
    try:
        return SlackWebhook.objects.get(organization=organization, admin=admin).webhook_url
    except SlackWebhook.DoesNotExist:
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
    get_obj=SlackWebhook.objects.filter(user=user).first()
    print("get_obj",get_obj)
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
    print("payload",payload)
    print("headers",headers)
    response = requests.post(url, headers=headers, json=payload)
    print("response",response)
    # return resp.json()
=======

def slack_notification(request,text,object,tag):
    redirect_url=redirect_from_slack_url(request,object)
    SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

    now = datetime.now()
    formatted = now.strftime("%B %d, %Y, %-I:%M %p")
    link_text = f"<{redirect_url}|{text}>"
    message = {
        "text": f"{formatted}: Asset {tag} {link_text}",
        # Optionally: "channel": "#your-channel", "username": "Notifier"
    }
    response = requests.post(SLACK_WEBHOOK_URL, json=message)
>>>>>>> 79fa78fa72d1913ae87d1a5c770f42762a4271ef
    if response.status_code == 200:
        print("Notification sent!")
        return HttpResponse("Notification sent!", status=200)
    else:
        print("Failed:", response.text)
        return HttpResponse("Failed to send notification", status=500)

<<<<<<< HEAD
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
        print(f"Channel {channel_name} created with ID: {channel_id}")
        return channel_id
    else:
        print(f"Failed to create channel: {data.get('error')}")
        return None
=======
def redirect_from_slack_url(request,obj_id):
    endpoint=f'/assets/details/{obj_id}'
    url=request.build_absolute_uri(endpoint)
    return url
    
>>>>>>> 79fa78fa72d1913ae87d1a5c770f42762a4271ef
