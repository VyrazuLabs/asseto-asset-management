from zoneinfo import ZoneInfo

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from assets.models import Asset
from configurations.utils import get_currency_and_datetime_format
from gate_pass.utils import get_gate_pass_list, search_and_filter_gate_passes
from common.body_validations import validate_body
from vendors.models import Vendor

from .models import GatePass

FIELDS = {
    "search": {"required": True},
    "movement_type": {"required": True},
    "destination_vendor": {"required": True},
    "expected_return_date": {"required": True},
}


@permission_required("gate_pass.view_gate_pass", raise_exception=True)
def listed(request):
    context = get_gate_pass_list()
    context["title"] = "Gate Passes"
    return render(request, "gate_pass/list.html", context=context)


@permission_required("gate_pass.view_gate_pass", raise_exception=True)
def filter_and_search(request):
    data = search_and_filter_gate_passes(request)
    return render(request, "gate_pass/search-data.html", {"data": data})


@permission_required("gate_pass.add_gate_pass", raise_exception=True)
def add(request):
    old = {}
    if request.method == "POST":
        if errors := validate_body(FIELDS, request.POST):
            return render(
                request,
                "gate_pass/add.html",
                {
                    "errors": errors,
                    "vendors": Vendor.undeleted_objects.all(),
                    "title": "Register New Gate Pass",
                    "old": request.POST,
                },
            )

        errors = {}
        search = request.POST.get("search", "").strip()
        movement_type = request.POST.get("movement_type")
        destination_vendor = request.POST.get("destination_vendor")
        expected_return_date = request.POST.get("expected_return_date")
        purpose_movement = request.POST.get("purpose-movement")

        vendor_name = ""
        if destination_vendor:
            try:
                vendor = Vendor.objects.get(id=destination_vendor)
                vendor_name = vendor.name
            except Vendor.DoesNotExist:
                errors["destination-vendor"] = (
                    f"Vendor with id '{destination_vendor}' does not exist."
                )

        old = {
            "search": search,
            "movement_type": movement_type,
            "destination_vendor": destination_vendor,
            "destination_vendor_name": vendor_name,
            "expected_return_date": expected_return_date,
            "purpose_movement": purpose_movement,
        }

        asset = Asset.objects.filter(
            Q(name__icontains=search) | Q(tag__icontains=search)
        ).first()

        if not asset:
            errors["search"] = "No asset found with this tag/name."
        elif GatePass.objects.filter(asset=asset, status=0).exists():
            errors["search"] = "This asset already has a pending gate pass."

        if errors:
            return render(
                request,
                "gate_pass/add.html",
                {
                    "errors": errors,
                    "vendors": Vendor.undeleted_objects.all(),
                    "title": "Register New Gate Pass",
                    "old": old,
                },
            )

        GatePass.objects.create(
            asset=asset,
            movement_type=movement_type,
            destination_vendor_id=destination_vendor,
            expected_return_date=expected_return_date,
            purpose_of_movement=purpose_movement or None,
            raised_by=request.user,
            authorised_by=None,
        )
        messages.success(request, "Gate pass created successfully")
        return redirect("gate_pass:list")

    vendors = Vendor.undeleted_objects.all()
    return render(
        request,
        "gate_pass/add.html",
        {
            "vendors": vendors,
            "title": "Register New Gate Pass",
            "errors": {},
            "old": old,
            "sidebar": "gate-pass",
        },
    )


@permission_required("gate_pass.view_gate_pass", raise_exception=True)
def detail(request, id):
    get_items = GatePass.objects.filter(id=id).first()
    obj = get_currency_and_datetime_format(request.user.organization)
    context = {
        "items": get_items,
        "currency": obj["currency"] if obj["currency"] else "INR",
        "title": "Gate Pass Detail",
        "sidebar": "gate-pass",
    }
    return render(request, "gate_pass/detail.html", context=context)


@permission_required("gate_pass.view_gate_pass", raise_exception=True)
def print_doc(request, id):
    gate_pass = GatePass.objects.filter(id=id).first()
    if not gate_pass:
        return HttpResponse("Gate Pass not found", status=404)

    checkout_url = request.build_absolute_uri(
        reverse("gate-pass:checkout", args=[gate_pass.id])
    )

    # Check if we are on localhost/127.0.0.1
    host = request.get_host().split(":")[0]
    is_local = host in ["127.0.0.1", "localhost"]

    context = {
        "gate_pass": gate_pass,
        "status": gate_pass.STATUS_CHOICES[gate_pass.status][1],
        "created_at": gate_pass.created_at.astimezone(ZoneInfo("Asia/Kolkata")).date(),
        "checkout_url": checkout_url,
        "is_local": is_local,
        "title": "Gate Pass Document",
    }
    return render(request, "gate_pass/print-doc.html", context=context)


# Deliberately ungated: the checkout link is shared with an external vendor
# via the printed/QR gate pass document, scanned without an app login.
def gate_pass_checkout(request, id):
    gate_pass = GatePass.objects.filter(id=id).first()
    if not gate_pass:
        return HttpResponse("Gate Pass not found", status=404)

    # [(0, 'Pending'), (1, 'Approved'), (2, 'Draft'), (3, 'Rejected'), (4, 'Checked Out')]
    if gate_pass.status == 4:
        return render(
            request,
            "gate_pass/public-checkout.html",
            {"gate_pass": gate_pass, "already_checked_out": True},
        )
    gate_pass.status = 4
    gate_pass.save()

    return render(
        request,
        "gate_pass/public-checkout.html",
        {"gate_pass": gate_pass, "already_checked_out": False},
    )


@permission_required("gate_pass.add_gate_pass", raise_exception=True)
def vendor_search(request):
    names = request.GET.get("q", "").strip()
    vendors = Vendor.undeleted_objects.filter(
        Q(name__icontains=names)
        | Q(email__icontains=names)
        | Q(gstin_number__icontains=names),
        organization=request.user.organization,
    )[:15]
    data = [
        {
            "id": str(vendor.id),
            "name": vendor.name,
            "email": vendor.email or "",
            "gstin": vendor.gstin_number or "",
        }
        for vendor in vendors
    ]
    return JsonResponse({"vendors": data})


@permission_required("gate_pass.authorise_gate_pass", raise_exception=True)
def authorisation(request, id, status):
    gate_pass = GatePass.objects.filter(id=id).first()
    if not gate_pass:
        return redirect("gate_pass:list")

    if status == 1:
        gate_pass.authorised_by = None
        gate_pass.status = 3
    else:
        gate_pass.authorised_by = request.user
        gate_pass.status = 1

    gate_pass.save()
    return redirect("gate_pass:list")


@permission_required("gate_pass.add_gate_pass", raise_exception=True)
def check_impact(request, tag):
    gate_pass = GatePass.objects.filter(asset__tag=tag).first()
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

    return JsonResponse(
        {"success": True, "count": total, "risk": "High" if total < 5 else "Low"}
    )
