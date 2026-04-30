from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import path
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
    filters=search_gate_passes(request)
    print("Filters Applied:", filters)
    if filters is not None:
        return render(request, 'gate_pass/search-data.html', {'filters': filters})
    else:
        get_obj=GatePass.objects.all()
        return render(request, 'gate_pass/search-data.html', {'items': get_obj})

def add(request):
    if request.method == 'POST':
        search = request.POST.get('search')
        movement_type = request.POST.get('movement-type')
        destination_vendor = request.POST.get('destination-vendor')
        expected_return_date = request.POST.get('expected-return-date')
        purpose_movement = request.POST.get('purpose-movement')
        # We are selecting the asset from the dropddown in the UI, So this method is mandatory
        asset = None
        if search:
            asset = Asset.objects.filter(
                Q(name__icontains=search) | Q(tag__icontains=search)
            ).first()

        print("Asset:", asset)

        if not asset:
            return HttpResponse("❌ Asset not found")  # DEBUG safety

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
    return render(request, 'gate_pass/add.html', {'vendors': vendors})

def detail(request,id):
    if request.method=='POST':
        status=request.POST.get('status')
        
        return redirect('gate_pass:list')
    get_items=GatePass.objects.filter(id=id).first()
    obj=get_currency_and_datetime_format(request.user.organization)
    #When went to the detail save the gatepass as draft if not authorised/unauthorised
    drafted=get_items.status
    if drafted==0:   #Save the gatepass object as drafted if its pending else not
        drafted=2    #Drafted gatepass
        get_items.status=drafted
        get_items.save()
    context={
        'items':get_items,
        'currency': obj['currency'] if obj['currency'] else 'INR',
        # 'datetime_format': obj['datetime_format'] if obj['datetime_format'] else '%Y-%m-%d %H:%M:%S',
    }
    # context=details_of_asset(request,id)
    # return render(request,'gate_pass/detail.html',context=context)
    return render(request,'gate_pass/detail.html',context=context)

def print_doc(request,id):
    gate_pass = GatePass.objects.filter(id=id).first()
    get_status=gate_pass.status
    print("Gate Pass Status:", gate_pass.STATUS_CHOICES[gate_pass.status][1])
    context={
        'gate_pass': gate_pass,
        'status': gate_pass.STATUS_CHOICES[gate_pass.status][1],
        'created_at': gate_pass.created_at.astimezone(ZoneInfo('Asia/Kolkata')).date(),
    }
    return render(request,'gate_pass/print-doc.html', context=context)

def authorisation(request,id,status):
    gate_pass = GatePass.objects.filter(id=id,status=status).first()
    if gate_pass.status==0: # Pending
        gate_pass.authorised_by = request.user
        gate_pass.status = 1  # Approved
        gate_pass.save()
    else:
        gate_pass.authorised_by = None
        gate_pass.status = 3  # Revert to Rejected
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
    print("Gate Pass Found:", gate_pass)
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