from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import path, reverse
from configurations.utils import get_currency_and_datetime_format
from products.models import ProductCategory
from upload.views.product_type_views import product_type_list
from .models import GatePass
from assets.models import Asset
from .forms import GatePassForm
from django.shortcuts import redirect
from vendors.models import Vendor
from django.db.models import Q, Count
import datetime
from zoneinfo import ZoneInfo
from gate_pass.utils import get_vendor_count,get_gate_pass_list, search_gate_passes
def listed(request):
    # gate_passes = GatePass.objects.all
    context=get_gate_pass_list(request)
    return render(request, 'gate_pass/list.html', context=context)

def search(request):
    filters = search_gate_passes(request)
    if filters is not None:
        return render(request, 'gate_pass/search-data.html', {'filters': filters})
    else:
        get_obj = GatePass.objects.all()
        return render(request, 'gate_pass/search-data.html', {'items': get_obj})

def add(request):
    errors = {}
    old = {}

    if request.method == 'POST':
        search = request.POST.get('search', '').strip()
        movement_type = request.POST.get('movement-type')
        destination_vendor = request.POST.get('destination-vendor')
        expected_return_date = request.POST.get('expected-return-date')
        purpose_movement = request.POST.get('purpose-movement')

        vendor_name = ''
        if destination_vendor:
            try:
                v = Vendor.objects.get(id=destination_vendor)
                vendor_name = v.name
            except Vendor.DoesNotExist:
                pass

        old = {
            'search': search,
            'movement_type': movement_type,
            'destination_vendor': destination_vendor,
            'destination_vendor_name': vendor_name,
            'expected_return_date': expected_return_date,
            'purpose_movement': purpose_movement,
        }

        if not search:
            errors['search'] = 'Please select an asset.'
        else:
            asset = Asset.objects.filter(
                Q(name__icontains=search) | Q(tag__icontains=search)
            ).first()
            if not asset:
                errors['search'] = 'No asset found with this tag/name.'
            elif GatePass.objects.filter(asset=asset, status=0).exists():
                errors['search'] = 'This asset already has a pending gate pass.'

        if not movement_type:
            errors['movement_type'] = 'Please select movement type.'

        if not destination_vendor:
            errors['destination_vendor'] = 'Please select a destination vendor.'

        if not expected_return_date:
            errors['expected_return_date'] = 'Please select expected return date.'

        if not errors:
            GatePass.objects.create(
                asset=asset,
                movement_type=movement_type,
                destination_vendor_id=destination_vendor,
                expected_return_date=expected_return_date,
                purpose_of_movement=purpose_movement or None,
                raised_by=request.user,
                authorised_by=None
            )
            return redirect('gate_pass:list')

    vendors = Vendor.undeleted_objects.all()
    return render(request, 'gate_pass/add.html', {
        'vendors': vendors,
        'title': 'Register New Gate Pass',
        'errors': errors,
        'old': old,
        'sidebar': 'gate-pass',
    })

def detail(request,id):
    if request.method=='POST':
        status=request.POST.get('status')
        
        return redirect('gate_pass:list')
    get_items = GatePass.objects.filter(id=id).first()
    obj = get_currency_and_datetime_format(request.user.organization)
    context = {
        'items': get_items,
        'currency': obj['currency'] if obj['currency'] else 'INR',
        'title': 'Gate Pass Detail',
        'sidebar': 'gate-pass',
    }
    return render(request, 'gate_pass/detail.html', context=context)

def print_doc(request,id):
    gate_pass = GatePass.objects.filter(id=id).first()
    if not gate_pass:
        return HttpResponse("❌ Gate Pass not found", status=404)
        
    get_status = gate_pass.status
    checkout_url = request.build_absolute_uri(reverse('gate-pass:checkout', args=[gate_pass.id]))
    
    # Check if we are on localhost/127.0.0.1
    host = request.get_host().split(':')[0]
    is_local = host in ['127.0.0.1', 'localhost']
    
    context={
        'gate_pass': gate_pass,
        'status': gate_pass.STATUS_CHOICES[gate_pass.status][1],
        'created_at': gate_pass.created_at.astimezone(ZoneInfo('Asia/Kolkata')).date(),
        'checkout_url': checkout_url,
        'is_local': is_local,
    }
    return render(request,'gate_pass/print-doc.html', context=context)

def gate_pass_checkout(request, id):
    gate_pass = GatePass.objects.filter(id=id).first()
    if not gate_pass:
        return HttpResponse("❌ Gate Pass not found", status=404)
    
    # Check if already checked out
    if gate_pass.status == 4:
        return render(request, 'gate_pass/public-checkout.html', {
            'gate_pass': gate_pass,
            'already_checked_out': True
        })

    # Update status to 'Checked Out' (4)
    gate_pass.status = 4
    gate_pass.save()
    
    return render(request, 'gate_pass/public-checkout.html', {
        'gate_pass': gate_pass,
        'already_checked_out': False
    })

def vendor_search(request):
    q = request.GET.get('q', '').strip()
    vendors = Vendor.undeleted_objects.filter(
        Q(name__icontains=q) | Q(email__icontains=q) | Q(gstin_number__icontains=q),
        organization=request.user.organization
    )[:15]
    data = [
        {
            'id': str(v.id), 
            'name': v.name, 
            'email': v.email or '', 
            'gstin': v.gstin_number or ''
        } for v in vendors
    ]
    return JsonResponse({'vendors': data})

def authorisation(request,id,status):
    gate_pass = GatePass.objects.filter(id=id).first()
    if not gate_pass:
        return redirect('gate_pass:list')

    if gate_pass.status == 1:  # Currently Approved
        gate_pass.authorised_by = None
        gate_pass.status = 3  # Set to Rejected/Revoked
    else:  # Currently Pending, Draft, or Rejected
        gate_pass.authorised_by = request.user
        gate_pass.status = 1  # Approve it
    
    gate_pass.save()
    return redirect('gate_pass:list')

# def check_impact(request,id):
#     gate_pass = GatePass.objects.filter(asset__tag=id).first()
#     asset = gate_pass.asset
#     base_query = ProductCategory.undeleted_objects.filter(organization=request.user.organization)
#     product_type_list = base_query.order_by('-created_at')
#     asset_counts = (
#         asset
#         .filter(
#             organization=request.user.organization,
#             product__product_type__in=product_type_list
#         )
#         .values("product__product_type")
#         .annotate(asset_count=Count("id", distinct=True))
#     )

#     product_category_asset_count = {
#         item['product__product_sub_category_id']: item['count']
#         for item in asset_counts
#     }
#     print(product_category_asset_count)
#     return product_category_asset_count

def check_impact(request, tag):
    gate_pass = GatePass.objects.filter(asset__tag=tag).first()
    if not gate_pass:
        return JsonResponse({"success": False, "message": "No asset found"})

    asset = gate_pass.asset

    asset_counts = (
        Asset.objects.filter(
            organization=request.user.organization,
            product__product_type=asset.product.product_type
        )
        .values("product__product_type")
        .annotate(count=Count("id"))
    )

    total = sum(item["count"] for item in asset_counts)

    return JsonResponse({
        "success": True,
        "count": total,
        "risk": "High" if total < 5 else "Low"
    })