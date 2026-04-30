from django.db.models import Count
from gate_pass.models import GatePass
import datetime
from zoneinfo import ZoneInfo
from authentication.models import User
from vendors.models import Vendor
from django.db.models import Q


def get_vendor_count(get_items):
    get_destination_vendor_list=get_items.values_list('destination_vendor__name',flat=True).distinct()
    total_vendor_count=get_items.values('destination_vendor__name').count()
    vendor_count = get_items.values('destination_vendor__name').annotate(count=Count('destination_vendor__name')/total_vendor_count*100).order_by('-count')
    print(vendor_count,total_vendor_count,get_destination_vendor_list)
    return vendor_count

def get_gate_pass_list(request):
    get_items=GatePass.objects.all()
    get_inward_pass_count=get_items.filter(movement_type=0).count()
    get_pending_authorization_count=get_items.filter(authorised_by=None).count()
    get_passes_created_today_count=get_items.filter(created_at__date=datetime.datetime.now(tz=ZoneInfo("Asia/Kolkata")).date()).count()
    #Filter By item List
    get_movement_type_list=get_items.values_list('movement_type',flat=True).distinct()
    raised_by_users = GatePass.objects.values('raised_by__id','raised_by__full_name').distinct()
    get_authorised_by_list=GatePass.objects.values('authorised_by__id','authorised_by__full_name').distinct()
    # get_destination_vendor_list=get_items.values_list('destination_vendor__name',flat=True).distinct()
    # get_destination_vendor_list=Vendor.undeleted_objects.all().values('name','id').distinct()
    get_destination_vendor_list=GatePass.objects.values('destination_vendor__id','destination_vendor__name').distinct()
    get_asset_list=GatePass.objects.values('asset_id','asset__name').distinct()
    # get_status_list=get_items.values_list('status',flat=True).distinct()
    get_status_list=GatePass.STATUS_CHOICES
    # get_asset_list=get_items.values_list('asset__name',flat=True).distinct()
    vendor_count = get_vendor_count(get_items)
    print("get_destination_vendor_list",get_destination_vendor_list)
    # Analytics
    # get_vendor_analytics
    print("adsdasdas",get_status_list)
    print("get_authorised_by_list",get_authorised_by_list)
    print("get_raised_by_list",raised_by_users)
    print("get_destination_vendor_list",get_destination_vendor_list)
    print("get_asset_list",get_asset_list)

    context={
        'vendor_count': vendor_count,
        'status_list':get_status_list,
        'authorised_by_list':get_authorised_by_list,
        'raised_by_list':raised_by_users,
        'destination_vendor_list':get_destination_vendor_list,
        'asset_list':get_asset_list,
        'movement_type_list':get_movement_type_list,
        'items':get_items,
        'inward_pass_count': get_inward_pass_count,
        'pending_authorization_count': get_pending_authorization_count,
        'passes_created_today_count': get_passes_created_today_count
    }
    return context

def get_users_from_id(id_list):
    user_list=User.objects.filter(id__in=id_list).values('id','full_name','email','phone')
    arr=[]
    user_dict={}
    for user in user_list:
        user_dict[user['id']]={
            'name':user['full_name'],
            'email':user['email'],
            'phone':user['phone']
        }
        arr.append(user_dict)
    return arr

def search_gate_passes(request):
    search = request.GET.get('search_text')
    print("Search Query:", search)
    movement_type = request.GET.get('type')
    print("Movement Type:", movement_type)
    raised_by = request.GET.get('raised_by',None) 
    destination_vendor = request.GET.get('vendor',None)
    expected_return_date = request.GET.get('expected-return-date')
    status=request.GET.get('status',None)
    asset=request.GET.get('asset',None)

    filters = GatePass.objects.filter(
        Q(asset__name__icontains=search) | 
        Q(asset__tag__icontains=search) | 
        Q(destination_vendor__name__icontains=search) | 
        Q(asset__serial_no__icontains=search) | 
        Q(raised_by__full_name__icontains=search) |
        Q(authorised_by__full_name__icontains=search) 
    )
    if status:
        filters=GatePass.objects.filter(status=status)
    if movement_type:
        filters = GatePass.objects.filter(movement_type=movement_type)
    if raised_by:     
        filters = GatePass.objects.filter(raised_by__id=raised_by)
    if destination_vendor:
        filters = GatePass.objects.filter(destination_vendor__id=destination_vendor)
    if expected_return_date:
        filters = GatePass.objects.filter(expected_return_date=expected_return_date)
    if asset:
        filters = GatePass.objects.filter(asset__id=asset)
    print("Filters Applied:", filters)
    return filters