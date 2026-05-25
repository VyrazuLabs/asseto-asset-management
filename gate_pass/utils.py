from django.db.models import Count, Q
from gate_pass.models import GatePass


def get_vendor_count(get_items):
    """Return vendor distribution as a list of {name, count%} dicts."""
    total_vendor_count = get_items.count()
    if total_vendor_count == 0:
        return []

    vendor_count = get_items.values('destination_vendor__name').annotate(
        count=Count('destination_vendor__name') * 100.0 / total_vendor_count
    ).order_by('-count')

    return vendor_count


def get_gate_pass_list(request):
    """Return context dict for the gate pass list template, scoped to the user's organization."""
    organization = request.user.organization
    get_items = GatePass.objects.filter(organization=organization).select_related(
        'asset', 'destination_vendor', 'raised_by', 'authorised_by'
    )

    get_inward_pass_count = get_items.filter(movement_type=1, status=1).count()
    get_pending_authorization_count = get_items.filter(status=0).count()

    from django.utils import timezone
    now = timezone.localtime(timezone.now())
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    get_passes_created_today_count = get_items.filter(created_at__gte=start_of_day).count()

    raised_by_users = get_items.values('raised_by__id', 'raised_by__full_name').distinct()
    get_authorised_by_list = get_items.values('authorised_by__id', 'authorised_by__full_name').distinct()
    get_destination_vendor_list = get_items.values('destination_vendor__id', 'destination_vendor__name').distinct()
    get_asset_list = get_items.values('asset_id', 'asset__name').distinct()
    get_movement_type_list = get_items.values_list('movement_type', flat=True).distinct()
    get_status_list = GatePass.STATUS_CHOICES
    vendor_count = get_vendor_count(get_items)

    return {
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
        'passes_created_today_count': get_passes_created_today_count,
    }


def search_gate_passes(request):
    """Filter GatePasses for the request user's organization by search text and field filters."""
    organization = request.user.organization
    search = (request.GET.get('search_text') or '').strip()
    movement_type = request.GET.get('type')
    raised_by = request.GET.get('raised_by')
    destination_vendor = request.GET.get('vendor')
    expected_return_date = request.GET.get('expected-return-date')
    status = request.GET.get('status')
    asset = request.GET.get('asset')

    filters = GatePass.objects.filter(organization=organization).select_related(
        'asset', 'destination_vendor', 'raised_by', 'authorised_by'
    )

    if search:
        filters = filters.filter(
            Q(asset__name__icontains=search) |
            Q(asset__tag__icontains=search) |
            Q(destination_vendor__name__icontains=search) |
            Q(asset__serial_no__icontains=search) |
            Q(raised_by__full_name__icontains=search) |
            Q(authorised_by__full_name__icontains=search)
        )
    if status:
        filters = filters.filter(status=status)
    if movement_type:
        filters = filters.filter(movement_type=movement_type)
    if raised_by:
        filters = filters.filter(raised_by__id=raised_by)
    if destination_vendor:
        filters = filters.filter(destination_vendor__id=destination_vendor)
    if expected_return_date:
        filters = filters.filter(expected_return_date=expected_return_date)
    if asset:
        filters = filters.filter(asset__id=asset)

    return filters


def create_gate_pass(request, movement_type, destination_vendor_id,
                     expected_return_date, purpose_movement, search):
    """Look up asset by name/tag and create a GatePass for the request user's org.

    Returns the created GatePass or None if the asset was not found.
    """
    from assets.models import Asset
    asset = None
    if search:
        asset = Asset.objects.filter(
            Q(name__icontains=search) | Q(tag__icontains=search),
            organization=request.user.organization,
        ).first()
    if not asset:
        return None

    return GatePass.objects.create(
        organization=request.user.organization,
        asset=asset,
        movement_type=movement_type,
        destination_vendor_id=destination_vendor_id,
        expected_return_date=expected_return_date or None,
        purpose_of_movement=purpose_movement or None,
        raised_by=request.user,
        authorised_by=None,
    )
