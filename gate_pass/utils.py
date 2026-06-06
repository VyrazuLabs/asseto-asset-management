from django.db.models import Count
from gate_pass.models import GatePass
import datetime
from zoneinfo import ZoneInfo
from authentication.models import User
from vendors.models import Vendor
from django.db.models import Q


def get_vendor_count(get_items):
    total_vendor_count = get_items.count()
    if total_vendor_count == 0:
        return []
    
    vendor_count = get_items.values('destination_vendor__name').annotate(
        count=Count('destination_vendor__name') * 100.0 / total_vendor_count
    ).order_by('-count')
    
    return vendor_count

def get_gate_pass_list(request):
    org = request.user.organization
    get_items = GatePass.objects.filter(asset__organization=org)
    get_inward_pass_count = get_items.filter(movement_type=1, status=1).count()
    get_pending_authorization_count = get_items.filter(status=0).count()
    from django.utils import timezone
    now = timezone.localtime(timezone.now())
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    get_passes_created_today_count = get_items.filter(created_at__gte=start_of_day).count()
    #Filter By item List
    get_movement_type_list = get_items.values_list('movement_type', flat=True).distinct()
    raised_by_users = get_items.values('raised_by__id', 'raised_by__full_name').distinct()
    get_authorised_by_list = get_items.values('authorised_by__id', 'authorised_by__full_name').distinct()
    get_destination_vendor_list = get_items.values('destination_vendor__id', 'destination_vendor__name').distinct()
    get_asset_list = get_items.values('asset_id', 'asset__name').distinct()
    get_status_list = GatePass.STATUS_CHOICES
    vendor_count = get_vendor_count(get_items)

    context = {
        'sidebar': 'gate-pass',
        'vendor_count': vendor_count,
        'status_list': get_status_list,
        'authorised_by_list': get_authorised_by_list,
        'raised_by_list': raised_by_users,
        'destination_vendor_list': get_destination_vendor_list,
        'asset_list': get_asset_list,
        'movement_type_list': get_movement_type_list,
        'items': get_items,
        'inward_pass_count': get_inward_pass_count,
        'pending_authorization_count': get_pending_authorization_count,
        'passes_created_today_count': get_passes_created_today_count
    }
    return context

def get_users_from_id(id_list):
    user_list = User.objects.filter(id__in=id_list).values('id', 'full_name', 'email', 'phone')
    arr = []
    user_dict = {}
    for user in user_list:
        user_dict[user['id']] = {
            'name': user['full_name'],
            'email': user['email'],
            'phone': user['phone']
        }
        arr.append(user_dict)
    return arr

def search_gate_passes(request):
    search = request.GET.get('search_text', '')
    movement_type = request.GET.get('type')
    raised_by = request.GET.get('raised_by', None)
    authorised_by = request.GET.get('authorised_by', None)
    destination_vendor = request.GET.get('vendor', None)
    expected_return_date = request.GET.get('expected-return-date')
    status = request.GET.get('status', None)
    asset = request.GET.get('asset', None)

    # Base Query — scoped to the user's organization
    org = request.user.organization
    filters = GatePass.objects.filter(asset__organization=org)

    # Search Filter
    if search:
        filters = filters.filter(
            Q(asset__name__icontains=search) |
            Q(asset__tag__icontains=search) |
            Q(destination_vendor__name__icontains=search) |
            Q(asset__serial_no__icontains=search) |
            Q(raised_by__full_name__icontains=search) |
            Q(authorised_by__full_name__icontains=search)
        )

    # Status Filter
    if status:
        filters = filters.filter(status=status)

    # Movement Type Filter
    if movement_type != "" and movement_type is not None:
        filters = filters.filter(movement_type=movement_type)

    # Raised By Filter
    if raised_by:
        filters = filters.filter(raised_by__id=raised_by)

    # Authorised By Filter
    if authorised_by:
        filters = filters.filter(authorised_by__id=authorised_by)

    # Vendor Filter
    if destination_vendor:
        filters = filters.filter(destination_vendor__id=destination_vendor)

    # Expected Return Date Filter
    if expected_return_date:
        filters = filters.filter(expected_return_date=expected_return_date)

    # Asset Filter
    if asset:
        filters = filters.filter(asset__id=asset)

    # Remove duplicates
    filters = filters.distinct().order_by('-created_at')

    return filters