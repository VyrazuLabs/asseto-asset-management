from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.db.models import Count
from zoneinfo import ZoneInfo

from configurations.utils import get_currency_and_datetime_format
from gate_pass.models import GatePass
from gate_pass.utils import get_gate_pass_list, search_gate_passes, create_gate_pass
from assets.models import Asset


@login_required
def listed(request):
    """Render the gate pass list page for the current user's organization."""
    context = get_gate_pass_list(request)
    return render(request, 'gate_pass/list.html', context=context)


@login_required
def search(request):
    """Return search-data partial template filtered by query params."""
    filters = search_gate_passes(request)
    return render(request, 'gate_pass/search-data.html', {'filters': filters})


@login_required
def add(request):
    """Render gate pass creation form; process POST to create a new gate pass."""
    from vendors.models import Vendor
    if request.method == 'POST':
        gate_pass = create_gate_pass(
            request,
            movement_type=request.POST.get('movement-type'),
            destination_vendor_id=request.POST.get('destination-vendor'),
            expected_return_date=request.POST.get('expected-return-date'),
            purpose_movement=request.POST.get('purpose-movement'),
            search=request.POST.get('search'),
        )
        if not gate_pass:
            return HttpResponse("Asset not found", status=404)
        return redirect('gate_pass:list')

    vendors = Vendor.undeleted_objects.filter(organization=request.user.organization)
    return render(request, 'gate_pass/add.html', {'vendors': vendors})


@login_required
def detail(request, id):
    """Render gate pass detail page."""
    get_items = GatePass.objects.filter(
        id=id, organization=request.user.organization
    ).select_related('asset', 'destination_vendor', 'raised_by', 'authorised_by').first()
    obj = get_currency_and_datetime_format(request.user.organization)
    context = {
        'items': get_items,
        'currency': obj['currency'] if obj['currency'] else 'INR',
    }
    return render(request, 'gate_pass/detail.html', context=context)


@login_required
def print_doc(request, id):
    """Render the printable gate pass document."""
    gate_pass = GatePass.objects.filter(
        id=id, organization=request.user.organization
    ).select_related('asset', 'destination_vendor', 'raised_by', 'authorised_by').first()
    context = {
        'gate_pass': gate_pass,
        'status': gate_pass.STATUS_CHOICES[gate_pass.status][1],
        'created_at': gate_pass.created_at.astimezone(ZoneInfo('Asia/Kolkata')).date(),
    }
    return render(request, 'gate_pass/print-doc.html', context=context)


@login_required
def authorisation(request, id, status):
    """Toggle approval/rejection of a gate pass."""
    gate_pass = GatePass.objects.filter(
        id=id, organization=request.user.organization
    ).first()
    if not gate_pass:
        return redirect('gate_pass:list')

    if gate_pass.status == 1:
        gate_pass.authorised_by = None
        gate_pass.status = 3
    else:
        gate_pass.authorised_by = request.user
        gate_pass.status = 1

    gate_pass.save()
    return redirect('gate_pass:list')


@login_required
def check_impact(request, tag):
    """Return JSON with asset count and risk level for a given asset tag."""
    gate_pass = GatePass.objects.filter(
        asset__tag=tag, organization=request.user.organization
    ).select_related('asset__product__product_type').first()
    if not gate_pass:
        return JsonResponse({"success": False, "message": "No asset found"})

    asset = gate_pass.asset
    asset_counts = (
        Asset.objects.filter(
            organization=request.user.organization,
            product__product_type=asset.product.product_type,
        )
        .values("product__product_type")
        .annotate(count=Count("id"))
    )

    total = sum(item["count"] for item in asset_counts)
    return JsonResponse({
        "success": True,
        "count": total,
        "risk": "High" if total < 5 else "Low",
    })
