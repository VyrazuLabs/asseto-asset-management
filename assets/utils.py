import json
import os
import random
import uuid
from django.http import JsonResponse
from django.utils import timezone
from audit.models import Audit, AuditImage
from configurations.models import TagConfiguration
from configurations.utils import dynamic_display_name, format_datetime, generate_asset_tag, get_currency_and_datetime_format
from .models import Asset,AssignAsset,AssetImage,AssetStatus,AssetStatusChoice,Location,Vendor,MaintenanceRecord
from dashboard.models import Department,ProductType,ProductCategory
from products.models import Product
from clients.models import Client
from .forms import AssetForm, AssignedAssetForm,ReassignedAssetForm,MaintenanceRecordForm
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from .models import Asset
from configurations.models import SlackConfiguration
from django.http import JsonResponse, HttpResponse
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import requests
from collections import defaultdict
from django.db import transaction
from django.db.models import Sum, Count, F, OuterRef, Subquery
from notifications.utils import notifications_call
from assets.barcode import generate_barcode
from .models import AssetSpecification

PAGE_SIZE = 25
ORPHANS = 1


def grouper(iterable, n):
    # Groups iterable into chunks of size n
    args = [iter(iterable)] * n
    return list(zip_longest(*args, fillvalue=None))


from itertools import zip_longest
from .models import Asset, AssignAsset
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from authentication.models import User

PAGE_SIZE = 25
ORPHANS = 1
MAX_FILTERED_RESULTS = 500


@login_required
@permission_required("assets.change_asset", raise_exception=True)
def release_asset(request, asset_id):
    if request.method == "POST":
        asset = get_object_or_404(Asset, pk=asset_id)
        asset.status = AssetStatusChoice.READY_TO_DEPLOY
        asset.save()
        messages.success(
            request,
            f"Asset '{asset.name}' has been released and is now Ready To Deploy.",
        )
    return redirect("assets:list")


@login_required
@permission_required("assets.change_asset", raise_exception=True)
def assign_asset(request, asset_id):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        asset = get_object_or_404(Asset, pk=asset_id)
        # Assumes you have a field like asset.assigned_user (ManyToOne/User FK)
        # User = get_user_model()
        selected_user = get_object_or_404(User, pk=user_id, is_active=True)
        asset.assigned_user = selected_user
        get_assigned_asset = AssignAsset.objects.filter(asset=asset).first()
        if get_assigned_asset is not None:
            asset.status = AssetStatusChoice.ASSIGNED
        asset.save()
        messages.success(
            request,
            f"Asset '{asset.name}' assigned to {selected_user.get_full_name() or selected_user.username}.",
        )
    return redirect("assets:list")


def get_asset_filter_data(request):
    product_category_list = ProductCategory.undeleted_objects.filter(
        Q(organization=None) | Q(organization=request.user.organization)
    )
    department_list = Department.undeleted_objects.filter(
        Q(organization=None) | Q(organization=request.user.organization)
    )
    location_list = Location.undeleted_objects.filter(
        Q(organization=None) | Q(organization=request.user.organization)
    )
    user_list = User.objects.filter(
        Q(organization=None) | Q(organization=request.user.organization), is_active=True
    ).order_by("-created_at")
    vendor_list = Vendor.objects.filter(
        Q(organization=None) | Q(organization=request.user.organization)
    ).order_by("-created_at")
    asset_status_list = AssetStatus.objects.filter(
        Q(organization=None) | Q(organization=request.user.organization)
    )
    product_type_list = ProductType.objects.filter(
        Q(organization=None) | Q(organization=request.user.organization)
    ).order_by("-created_at")
    asset_list = Asset.undeleted_objects.filter(
        Q(organization=None) | Q(organization=request.user.organization)
    ).order_by("-created_at")
    deleted_asset_count = Asset.deleted_objects.filter(
        organization=request.user.organization
    ).count()
    get_assigned_asset_list = (
        AssignAsset.objects.select_related("user")
        .filter(
            Q(asset__in=asset_list) & Q(asset__organization=None)
            | Q(asset__organization=request.user.organization)
        )
        .order_by("-assigned_date")
    )
    asset_user_map = {}
    for assign in get_assigned_asset_list:
        if assign.asset_id not in asset_user_map:
            asset_user_map[assign.asset_id] = None
        if assign.user:
            asset_user_map[assign.asset_id] = {
                "full_name": assign.user.full_name,
                "image": assign.user.profile_pic,
            }
    paginator = Paginator(asset_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)
    asset_form = AssetForm(organization=request.user.organization)
    assign_asset_form = AssignedAssetForm(organization=request.user.organization)
    reassign_asset_form = ReassignedAssetForm(organization=request.user.organization)
    active_users = User.objects.filter(
        is_active=True, organization=request.user.organization
    )
    asset_ids_in_page = [asset.id for asset in page_object]
    # Newest image per asset, decided in SQL instead of reducing all rows in Python
    asset_images = first_image_map(asset_ids_in_page)
    return {
        "product_category_list": product_category_list,
        "department_list": department_list,
        "location_list": location_list,
        "asset_user_map": asset_user_map,
        "product_type_list": product_type_list,
        "asset_status_list": asset_status_list,
        "user_list": user_list,
        "vendor_list": vendor_list,
        "active_user": active_users,
        "sidebar": "assets",
        "submenu": "list",
        "asset_images": asset_images,  # dict {asset.id: first AssetImage instance}
        "page_object": page_object,
        "asset_form": asset_form,
        "assign_asset_form": assign_asset_form,
        "reassign_asset_form": reassign_asset_form,
        "deleted_asset_count": deleted_asset_count,
        "title": "Assets",
    }


def filtered_asset(request):
    user_data = request.POST.get("user-data")
    client_data = request.POST.get("client-data")
    product_type = request.POST.get("product_type")  # gets the id of the product type
    search_text = (request.GET.get("search_text") or "").strip()
    vendor_id = request.GET.get("vendor")
    status_name = request.GET.get("status")
    department_id = request.GET.get("department")
    location_id = request.GET.get("location")
    category_id = request.GET.get("category")
    product_type_id = request.GET.get("product_type")
    client_id = request.GET.get("client")
    # org="4fdbba1a0f1e48bf9ae9c1de5a98e0bd"
    filters = Q(
        organization=request.user.organization if request.user.organization else None
    )
    # filters = Q(organization=None)
    if search_text:
        filters &= (
            Q(tag__icontains=search_text)
            | Q(name__icontains=search_text)
            | Q(serial_no__icontains=search_text)
            | Q(purchase_type__icontains=search_text)
            | Q(product__product_type__name__icontains=search_text)
            | Q(vendor__name__icontains=search_text)
            | Q(vendor__gstin_number__icontains=search_text)
            | Q(location__office_name__icontains=search_text)
            | Q(client__name__icontains=search_text)
        )

    if vendor_id:
        filters &= Q(vendor_id=vendor_id)
    if status_name:
        try:
            uuid.UUID(str(status_name))
            filters &= Q(asset_status_id=status_name)
        except (ValueError, TypeError, AttributeError):
            filters &= Q(asset_status__name__icontains=status_name)
    if category_id:
        filters &= Q(product__product_sub_category_id=category_id)
    if product_type_id:
        filters &= Q(product__product_type_id=product_type_id)
    if client_id:
        try:
            client_obj = Client.undeleted_objects.filter(id=client_id).first()
            if client_obj:
                same_name_ids = list(
                    Client.undeleted_objects.filter(
                        organization=request.user.organization,
                        name__iexact=client_obj.name,
                    ).values_list("id", flat=True)
                )
                filters &= Q(client_id__in=same_name_ids)
            else:
                filters &= Q(client_id=client_id)
        except Exception:
            filters &= Q(client_id=client_id)
    if location_id:
        filters &= Q(location_id=location_id)

    is_assigned = request.GET.get("is_assigned")
    if is_assigned == 'true':
        filters &= Q(is_assigned=True)
    elif is_assigned == 'false':
        filters &= Q(is_assigned=False)

    assets_qs = Asset.undeleted_objects.filter(filters).select_related('location', 'product__product_type', 'vendor', 'client', 'asset_status').order_by("-created_at")

    # Scoped to assets currently assigned to the requesting user unless
    # they hold "assets.all_asset" (superusers always pass via Django's
    # has_perm) — without it, a non-superuser saw every asset in the org
    # regardless of who it was assigned to. distinct() guards against
    # duplicate rows from an asset with more than one AssignAsset record
    # (e.g. reassignment history).
    if not request.user.has_perm("assets.all_asset"):
        assets_qs = assets_qs.filter(assignasset__user=request.user).distinct()

    # Filter by product type
    if product_type:
        assets_qs = assets_qs.filter(product__product_type_id=product_type)
    if user_data:
        assigned_qs = (
            AssignAsset.objects.filter(user_id=user_data)
            .select_related("user")
            .order_by("-assigned_date")
        )
        assets_qs = assets_qs.filter(assignasset__user=user_data).prefetch_related(
            Prefetch("assignasset_set", queryset=assigned_qs, to_attr="assignments")
        )
    if client_data:
        assets_qs = assets_qs.filter(client_id=client_data)
    if department_id:
        assigned_qs = AssignAsset.objects.filter(user__department_id=department_id)
        assets_qs = assets_qs.filter(assignasset__user__department_id=department_id)

    return assets_qs


def create_asset_list(request, assets_qs):
    org_filter = Q(organization=None) | Q(organization=request.user.organization)
    visible_asset_ids = list(
        Asset.undeleted_objects.filter(org_filter).values_list("id", flat=True)
    )
    audits_for_org = (
        Audit.objects.filter(asset_id__in=visible_asset_ids)
        .values("asset_id", "condition")
    )
    asset_conditions_map = defaultdict(list)
    audited_asset_ids = set()
    for row in audits_for_org:
        asset_conditions_map[row["asset_id"]].append(row["condition"])
        audited_asset_ids.add(row["asset_id"])

    list_of_audited_assets = Asset.undeleted_objects.filter(id__in=audited_asset_ids)
    product_category_list = ProductCategory.undeleted_objects.filter(org_filter)
    department_list = Department.undeleted_objects.filter(org_filter)
    location_list = Location.undeleted_objects.filter(org_filter)
    user_list = User.objects.filter(org_filter, is_active=True).order_by("-created_at")
    vendor_list = Vendor.objects.filter(org_filter).order_by("-created_at")
    asset_status_list = AssetStatus.objects.filter(org_filter)
    product_type_list = ProductType.undeleted_objects.filter(org_filter).order_by("-created_at")
    product_list = Product.undeleted_objects.filter(org_filter).order_by("-created_at")
    raw_client_list = Client.undeleted_objects.filter(
        organization=request.user.organization
    ).order_by("-created_at")
    seen_client_names = set()
    client_list = []
    for c in raw_client_list:
        clean_name = (c.name or "").strip().lower()
        if clean_name not in seen_client_names:
            seen_client_names.add(clean_name)
            client_list.append(c)
    asset_list = Asset.undeleted_objects.filter(org_filter).select_related('location', 'product__product_type').order_by("-created_at")
    if not request.user.has_perm("assets.all_asset"):
        asset_list = asset_list.filter(assignasset__user=request.user).distinct()
    deleted_asset_count = Asset.deleted_objects.filter(
        organization=request.user.organization
    ).count()
    paginator = Paginator(assets_qs, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)
    # Only the rows actually rendered on this page need an assigned-user map or
    # a thumbnail, so both queries are scoped to these ids — they stay
    # page-sized instead of loading every assignment in the organisation.
    asset_ids_in_page = [asset.id for asset in page_object]

    get_assigned_asset_list = (
        AssignAsset.objects.select_related("user")
        .filter(asset_id__in=asset_ids_in_page)
        .order_by("-assigned_date")
    )
    asset_user_map = {}
    for assign in get_assigned_asset_list:
        if assign.asset_id not in asset_user_map:
            if assign.user:
                asset_user_map[assign.asset_id] = {
                    "full_name": dynamic_display_name(
                        request, fullname=assign.user.full_name
                    ),
                    "image": assign.user.profile_pic,
                    "assign_id": assign.id,
                }
            else:
                asset_user_map[assign.asset_id] = None
    asset_form = AssetForm(organization=request.user.organization)
    assign_asset_form = AssignedAssetForm(organization=request.user.organization)
    reassign_asset_form = ReassignedAssetForm(organization=request.user.organization)
    active_users = User.objects.filter(
        is_active=True, organization=request.user.organization
    )
    # Newest image per asset, decided in SQL instead of reducing all rows in Python
    asset_images = first_image_map(asset_ids_in_page)
    is_demo = bool(os.environ.get("IS_DEMO"))
    # Stats for summary cards – scoped like the list. One aggregate pass
    # replaces the three separate count/aggregate queries that used to run here.
    stats = asset_list.aggregate(
        total=Sum("price"),
        active_count=Count("id"),
        assigned_count=Count("id", filter=Q(is_assigned=True)),
    )
    total_value = stats["total"] or 0
    active_count = stats["active_count"]
    assigned_count = stats["assigned_count"]

    context = {
        "product_category_list": product_category_list,
        "department_list": department_list,
        "location_list": location_list,
        "asset_user_map": asset_user_map,
        "product_type_list": product_type_list,
        "product_list": product_list,
        "client_list": client_list,
        "has_clients": bool(client_list),
        "asset_status_list": asset_status_list,
        "user_list": user_list,
        "vendor_list": vendor_list,
        "active_user": active_users,
        "sidebar": "assets",
        "submenu": "list",
        "asset_images": asset_images,
        "page_object": page_object,
        "asset_form": asset_form,
        "assign_asset_form": assign_asset_form,
        "reassign_asset_form": reassign_asset_form,
        "deleted_asset_count": deleted_asset_count,
        "total_value": total_value,
        "active_count": active_count,
        "assigned_count": assigned_count,
        "title": "Assets",
        "is_demo": is_demo,
        "list_of_audited_assets": list_of_audited_assets,
        "asset_conditions_map": asset_conditions_map,
    }
    return context


def assign_asset(request, id):
    user_id = request.POST.get("user_id")
    asset = get_object_or_404(Asset, pk=id, organization=request.user.organization)
    selected_user = get_object_or_404(User, pk=user_id, is_active=True)

    # Create or update the AssignAsset record
    assign_obj, created = AssignAsset.objects.update_or_create(
        asset=asset,
        defaults={"user": selected_user},
    )
    # Mark asset as assigned
    asset.is_assigned = True
    set_asset = AssetStatus.objects.filter(
        Q(organization=request.user.organization) | Q(organization__isnull=True),
        name="Assigned",
    ).first()
    asset.asset_status = set_asset
    # asset.status = 0  # 0 = 'Assigned' by your STATUS_CHOICES
    asset.save()


@transaction.atomic
def assign_asset_in_form(request, form):
    asset = form.instance.asset
    asset.is_assigned = True
    set_asset_status = AssetStatus.objects.filter(
        Q(organization=request.user.organization) | Q(organization__isnull=True),
        name="Assigned",
    ).first()
    asset.asset_status = set_asset_status
    asset.save()
    # form.save_m2m()
    form.save()

    # Save uploaded images related to the asset
    for f in request.FILES.getlist("image"):
        AssetImage.objects.create(asset=asset, image=f)
    messages.success(request, "Asset assigned to user successfully")
    slack_notification(
        request, f"{asset.name}  assigned successfully to user", asset.id, asset.tag
    )
    notifications_call(
        user=request.user,
        entity_type=2,
        notification_text=f"{asset.name}  assigned successfully to user",
        notification_title="Asset Assigned",
    )


@transaction.atomic
def delete_assign_asset(request, id):
    assignAsset = get_object_or_404(
        AssignAsset, pk=id, asset__organization=request.user.organization
    )
    assignAsset.delete()
    assignAsset.asset.is_assigned = False
    set_asset = AssetStatus.objects.filter(
        Q(organization=request.user.organization) | Q(organization__isnull=True),
        name="Available",
    ).first()
    assignAsset.asset.asset_status = set_asset
    assignAsset.asset.save()
    messages.success(request, "Asset unassigned successfully")


def get_audit_images(asset_id):
    audit_images = (
        AuditImage.objects.filter(audit__asset__id=asset_id)
        .order_by("-uploaded_at")
        .first()
    )
    return audit_images


def get_asset_images(asset):
    images = AssetImage.objects.filter(asset=asset).order_by("-uploaded_at").values()
    return images


def first_image_map(asset_ids):
    """Map asset.id -> newest AssetImage, decided in SQL (one query)."""
    asset_ids = list(asset_ids)
    if not asset_ids:
        return {}
    newest = AssetImage.objects.filter(asset_id=OuterRef("asset_id")).order_by(
        "-uploaded_at"
    )
    rows = AssetImage.objects.filter(asset_id__in=asset_ids).annotate(
        newest_pk=Subquery(newest.values("pk")[:1])
    ).filter(pk=F("newest_pk"))
    return {img.asset_id: img for img in rows}


def details_of_asset(request, id):
    get_audit_history = Audit.objects.filter(asset_id=id).select_related("asset").prefetch_related(
        Prefetch(
            "images",
            queryset=AuditImage.objects.order_by("-uploaded_at"),
            to_attr="prefetched_images",
        )
    )
    asset = get_object_or_404(
        Asset.objects
        .select_related("product__product_type", "vendor", "location", "asset_status", "client", "organization"),
        pk=id,
        organization=request.user.organization,
    )
    assigned_asset = AssignAsset.objects.select_related("user").filter(asset=asset).first()
    assetSpecifications = AssetSpecification.objects.filter(asset=asset)
    get_asset_img = get_asset_images(asset)
    asset_barcode = generate_barcode(asset.tag)
    maintenance_records = MaintenanceRecord.objects.filter(asset=asset).order_by('-created_at')
    maintenance_form = MaintenanceRecordForm(organization=request.user.organization)
    context=asset_details(request,get_audit_history,asset,assigned_asset,assetSpecifications,get_asset_img,asset_barcode,maintenance_records,maintenance_form)
    return context

def asset_details(request,get_audit_history,asset,assigned_asset,assetSpecifications,get_asset_img,asset_barcode,maintenance_records=None,maintenance_form=None):
    audit_data = []
    if get_audit_history:
        for audit in get_audit_history:
            if hasattr(audit, "prefetched_images"):
                audit_image = audit.prefetched_images[0] if audit.prefetched_images else None
            else:
                audit_image = (
                    AuditImage.objects.filter(audit=audit)
                    .order_by("-uploaded_at")
                    .first()
                )
            data = {
                "id": audit.id,
                "asset_name": audit.asset.name,
                "condition_label": audit.condition_label,
                "notes": audit.notes,
                "created_at": audit.created_at,
                "audit_image": audit_image,
            }
            audit_data.append(data)

    if assigned_asset and assigned_asset.user:
        assigned_user = assigned_asset.user.full_name
    else:
        assigned_user = None

    img_array = []

    for it in get_asset_img:
        img_array.append(it)
    months_int = asset.product.eol if asset.product else None
    today = timezone.now().date()
    if months_int:
        eol_date = today + relativedelta(months=months_int)
    else:
        eol_date = None
    arr_size = len(img_array)
    history_list = asset.history.all().order_by("-history_date", "-history_id")
    paginator = Paginator(history_list, 5, orphans=1)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)
    from custom_fields.utils import get_definitions_for_module, get_values_for_entity
    cf_definitions = get_definitions_for_module(request.user.organization, "asset")
    cf_values = get_values_for_entity(asset.id, cf_definitions)
    organization = request.user.organization
    obj = get_currency_and_datetime_format(organization)
    get_currency = obj["currency"]
    get_date_format = obj["date_format"]
    is_demo = bool(os.environ.get("IS_DEMO"))
    if get_date_format:
        asset.warranty_expiry_date = (
            format_datetime(x=asset.warranty_expiry_date, output_format=get_date_format)
            if asset.warranty_expiry_date is not None
            else ""
        )
        asset.purchase_date = (
            format_datetime(x=asset.purchase_date, output_format=get_date_format)
            if asset.purchase_date is not None
            else ""
        )
        eol_date = (
            format_datetime(x=eol_date, output_format=get_date_format)
            if eol_date is not None
            else ""
        )
    cf_values_formatted = {}
    for defn in cf_definitions:
        val = cf_values.get(defn.field_key)
        if val and defn.field_type == 'date' and get_date_format:
            cf_values_formatted[defn.field_key] = format_datetime(x=val, output_format=get_date_format)
        else:
            cf_values_formatted[defn.field_key] = val


    from authentication.models import User, Technician
    
    maintenance_type_labels = {
        '1': 'Calibration',
        '2': 'Breakdown',
        '3': 'Preventive',
        '4': 'Repair',
        '5': 'Other',
    }
    
    status_labels = {
        '1': 'New',
        '2': 'In Progress',
        '3': 'Completed',
    }
    
    technician_map = {}
    # Fetch all users for name resolution, regardless of active status
    tech_users = User.undeleted_objects.filter(
        organization=request.user.organization
    )
    for u in tech_users:
        display_name = u.reverse_full_name or u.full_name or u.email
        technician_map[str(u.id)] = display_name

    # Also map Technician IDs to name resolution
    for tech in Technician.objects.select_related('user').filter(user__organization=request.user.organization):
        display_name = tech.user.reverse_full_name or tech.user.full_name or tech.user.email
        technician_map[str(tech.id)] = display_name

    maintenance_history_entries = []
    if maintenance_records:
        records = list(maintenance_records)

        # Load every record's audit trail in ONE query instead of one query per
        # record (the historical rows are keyed by the original `id`).
        history_map = None
        records_with_trail = [r for r in records if r.updated_by]
        if records_with_trail:
            try:
                trail_model = MaintenanceRecord.history.model
                history_map = defaultdict(list)
                for h in trail_model.objects.filter(
                    id__in=[r.id for r in records_with_trail]
                ).order_by("history_date", "history_id"):
                    history_map[h.id].append(h)
            except Exception:
                history_map = None

        for record in records:
            maintenance_history_entries.append({
                'type': 'created',
                'timestamp': record.created_at,
                'user_id': record.created_by,
                'details': maintenance_type_labels.get(record.maintenance_type, record.maintenance_type),
            })
            if not record.updated_by:
                continue
            if history_map is None:
                maintenance_history_entries.append({
                    'type': 'updated',
                    'timestamp': record.updated_at,
                    'user_id': record.updated_by,
                    'details': 'Maintenance',
                })
                continue
            prev = None
            for h in history_map.get(record.id, ()):
                if h.history_type == '~' and prev:
                    changes = []
                    if h.technician != prev.technician:
                        changes.append('Technician')
                    if h.status != prev.status:
                        changes.append('Status')
                    if changes:
                        maintenance_history_entries.append({
                            'type': 'updated',
                            'timestamp': h.history_date,
                            'user_id': h.updated_by,
                            'details': ', '.join(changes),
                        })
                prev = h

    context = {'title': 'Asset Details', 'sidebar': 'assets', 'assigned_user':assigned_user,'assigned_asset':assigned_asset,'asset_barcode':asset_barcode,'asset': asset, 'submenu': 'list', 'page_object': page_object,'arr_size':arr_size,
               'maintenance_records': maintenance_records, 'maintenance_form': maintenance_form, 'maintenance_type_labels': maintenance_type_labels, 'status_labels': status_labels, 'technician_map': technician_map, 'maintenance_history_entries': maintenance_history_entries,
               'cf_definitions': cf_definitions, 'cf_values': cf_values, 'cf_values_formatted': cf_values_formatted, 'get_asset_img': get_asset_img, 'get_audit_history': get_audit_history, 'audit_data': audit_data, 'assetSpecifications': assetSpecifications, 'get_date_format': get_date_format, 'get_currency': get_currency, 'eol_date': eol_date, 'is_demo': is_demo}

    return context


@transaction.atomic
def add_asset(request, form):
    asset = form.save(commit=False)
    asset.organization = request.user.organization
    asset.created_by = str(request.user.id)
    available_status = AssetStatus.objects.filter(name="Available").first()
    asset.asset_status = available_status
    asset.save()
    form.save_m2m()
    # Save images
    for image_file in request.FILES.getlist("image"):
        AssetImage.objects.create(asset=asset, image=image_file)


    slack_notification(
        request, f"{asset.name}  added successfully", asset.id, asset.tag
    )


def search_asset(request):
    org_filter = Q(organization=None) | Q(organization=request.user.organization)
    visible_asset_ids = list(
        Asset.undeleted_objects.filter(org_filter).values_list("id", flat=True)
    )
    audits_for_org = (
        Audit.objects.filter(asset_id__in=visible_asset_ids)
        .values("asset_id", "condition")
    )
    asset_conditions_map = defaultdict(list)
    audited_asset_ids = set()
    for row in audits_for_org:
        asset_conditions_map[row["asset_id"]].append(row["condition"])
        audited_asset_ids.add(row["asset_id"])

    list_of_audited_assets = Asset.undeleted_objects.filter(id__in=audited_asset_ids)
    context = search_with_filters(request, list_of_audited_assets, asset_conditions_map)
    return context


def search_with_filters(request, list_of_audited_assets, asset_conditions_map):
    search_text = (request.GET.get("search_text") or "").strip()
    vendor_id = request.GET.get("vendor")
    status_value = request.GET.get("status")
    user_id = request.GET.get("user")
    department_id = request.GET.get("department")
    product_category_id = request.GET.get("category")
    product_type_id = request.GET.get("product_type")
    client_id = request.GET.get("client")
    location_id = request.GET.get("location")
    is_assigned = request.GET.get("is_assigned")

    # Start query
    q = Q(organization=request.user.organization)

    # Apply filters if present
    if search_text:
        q &= (
            Q(name__icontains=search_text)
            | Q(serial_no__icontains=search_text)
            | Q(purchase_type__icontains=search_text)
            | Q(product__product_type__name__icontains=search_text)
            | Q(vendor__name__icontains=search_text)
            | Q(vendor__gstin_number__icontains=search_text)
            | Q(location__office_name__icontains=search_text)
            | Q(client__name__icontains=search_text)
            | Q(tag__icontains=search_text)
        )

    if vendor_id:
        q &= Q(vendor_id=vendor_id)

    if status_value:
        import uuid
        try:
            uuid.UUID(str(status_value))
            q &= Q(asset_status_id=status_value)
        except ValueError:
            q &= Q(asset_status__name__iexact=status_value)

    if product_category_id:
        q &= Q(product__product_sub_category_id=product_category_id)

    if product_type_id:
        q &= Q(product__product_type_id=product_type_id)

    if client_id:
        try:
            client_obj = Client.undeleted_objects.filter(id=client_id).first()
            if client_obj:
                same_name_ids = list(
                    Client.undeleted_objects.filter(
                        organization=request.user.organization,
                        name__iexact=client_obj.name,
                    ).values_list("id", flat=True)
                )
                q &= Q(client_id__in=same_name_ids)
            else:
                q &= Q(client_id=client_id)
        except Exception:
            q &= Q(client_id=client_id)
    if location_id:
        q &= Q(location_id=location_id)
    if is_assigned == "true":
        q &= Q(is_assigned=True)
    elif is_assigned == "false":
        q &= Q(is_assigned=False)

    # Scope to assigned assets unless user has all_asset
    if not request.user.has_perm("assets.all_asset"):
        q &= Q(assignasset__user=request.user)

    if user_id:
        assigned_qs = (
            AssignAsset.objects.filter(user_id=user_id)
            .select_related("user")
            .order_by("-assigned_date")
        )
        search_qs = (
            Asset.undeleted_objects.filter(q, assignasset__user_id=user_id)
            .select_related('location', 'product__product_type', 'vendor', 'client', 'asset_status')
            .prefetch_related(
                Prefetch("assignasset_set", queryset=assigned_qs, to_attr="assignments")
            )
            .order_by("-created_at")
        )
    elif department_id:
        search_qs = Asset.undeleted_objects.filter(
            q, assignasset__user__department_id=department_id
        ).select_related('location', 'product__product_type', 'vendor', 'client', 'asset_status').order_by("-created_at")
    else:
        search_qs = Asset.undeleted_objects.filter(q).select_related('location', 'product__product_type', 'vendor', 'client', 'asset_status').order_by("-created_at")

    # If any search/filter is active, skip the small per-page cap so matches
    # aren't hidden behind pages, but still bound the result set — an
    # unfiltered browse view uses regular pagination below.
    any_filter_active = any([
        search_text, vendor_id, status_value, user_id, department_id,
        product_category_id, product_type_id, client_id, location_id,
        is_assigned,
    ])

    if any_filter_active:
        search_qs = search_qs.distinct()
    paginator = Paginator(search_qs, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    asset_ids = [asset.id for asset in page_object]
    asset_images = first_image_map(asset_ids)
    asset_user_map = {}
    get_assigned_asset_list = (
        AssignAsset.objects.select_related("user")
        .filter(asset_id__in=asset_ids, asset__organization=request.user.organization)
        .order_by("-assigned_date")
    )
    for assign in get_assigned_asset_list:
        if assign.asset_id not in asset_user_map:
            asset_user_map[assign.asset_id] = None
        if assign.user:  # avoid None users
            asset_user_map[assign.asset_id] = {
                "full_name": dynamic_display_name(
                    request, fullname=assign.user.full_name
                ),
                "image": assign.user.profile_pic,
                "assign_id": assign.id,
            }

    has_clients = Client.undeleted_objects.filter(
        organization=request.user.organization
    ).exists()
    context = {
        "page_object": page_object,
        "asset_user_map": asset_user_map,
        "asset_images": asset_images,
        "list_of_audited_assets": list_of_audited_assets,
        "asset_conditions_map": asset_conditions_map,
        "has_clients": has_clients,
        "asset_form": AssetForm(organization=request.user.organization),
        "is_demo": bool(os.environ.get("IS_DEMO")),
    }
    return context


def autogenerated_tag(request, form):
    tag_config = TagConfiguration.objects.filter(
        organization=request.user.organization, use_default_settings=True
    ).first()
    if tag_config:
        form.data["tag"] = generate_asset_tag(
            prefix=tag_config.prefix, number_suffix=tag_config.number_suffix
        )
    else:
        form.data["tag"] = generate_asset_tag(prefix="VY", number_suffix="001")


def create_char_data(data):
    if not data:
        return [["Status", "Assets"], ["Assigned", 0], ["Unassigned", 0]]
    assigned = sum(1 for asset in data if asset.is_assigned)
    unassigned = sum(1 for asset in data if not asset.is_assigned)
    return [
        ["Status", "Assets"],
        ["Assigned", assigned],
        ["Unassigned", unassigned],
    ]


def delete_asset_images(request, asset):
    try:
        data = json.loads(request.body)
        delete_ids = data.get("delete_image_ids", [])

        if not delete_ids:
            return JsonResponse(
                {"success": False, "message": "No image IDs provided."}, status=400
            )

        AssetImage.objects.filter(id__in=delete_ids, asset=asset).delete()
        return JsonResponse(
            {"success": True, "message": "Images deleted successfully."}
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON."}, status=400)


def save_new_images(request, asset):
    for img in request.FILES.getlist("image"):
        AssetImage.objects.create(asset=asset, image=img)


    pass


# Previous Workflow
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


def set_slack_webhook(organization, admin, url):
    obj, created = SlackConfiguration.objects.update_or_create(
        organization=organization,
        admin=admin,
        defaults={"webhook_url": url},
    )


def get_slack_webhook_url(organization, admin):
    try:
        return SlackConfiguration.objects.get(
            organization=organization, admin=admin
        ).webhook_url
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


# New Integrations
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


# New Integrations with slack bot
def slack_notification(request, text, object, tag):
    user = request.user
    get_obj = SlackConfiguration.objects.filter(user=user).first()
    bot_token = None
    channel_id = None
    if get_obj is not None:
        bot_token = get_obj.access_token
        channel_id = get_obj.channel_id
    else:
        return HttpResponse("Slack not configured for user", status=400)
    now = datetime.now()
    redirect_url = redirect_from_slack_url(request, object)
    formatted = now.strftime("%B %d, %Y, %-I:%M %p")

    link_text = f"<{redirect_url}|{text}>"
    message = f"{formatted}: Asset {tag} {link_text}"
    # Optionally: "channel": "#your-channel", "username": "Notifier"
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {bot_token}"}
    payload = {"channel": channel_id, "text": message}  # channel_id, not name!
    response = requests.post(url, headers=headers, json=payload)
    # return resp.json()
    if response.status_code == 200:
        return HttpResponse("Notification sent!", status=200)
    else:
        return HttpResponse("Failed to send notification", status=500)


# Make a new slack channelfrom scratch.
def create_slack_channel(bot_token, channel_name):
    url = "https://slack.com/api/conversations.create"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
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


def redirect_from_slack_url(request, obj_id):
    endpoint = f"/assets/details/{obj_id}"
    url = request.build_absolute_uri(endpoint)
    return url


def get_host(request):
    endpoint = f"/assets/list"
    host = request.build_absolute_uri(endpoint)
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


def get_asset_status_list_utils(request, page_number=None):
    """
    Returns:
        page_object,
        asset_status_asset_count (dict),
        stats (dict)
    """

    search_text = request.GET.get("search_text", "").strip()
    status = request.GET.get("status", "")

    # BASE QUERY
    base_query = AssetStatus.undeleted_objects.filter(
        Q(organization=None) | Q(organization=request.user.organization)
    )

    # STATS — single scan for total/active/inactive (deleted uses another queryset)
    status_counts = base_query.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=True)),
        inactive=Count("id", filter=Q(status=False)),
    )
    total_statuses = status_counts["total"]
    active_statuses = status_counts["active"]
    inactive_statuses = status_counts["inactive"]
    deleted_statuses_count = AssetStatus.deleted_objects.filter(
        Q(organization=None, can_modify=True)
        | Q(organization=request.user.organization, can_modify=True)
    ).count()

    # SEARCH FILTER
    if search_text:
        base_query = base_query.filter(name__icontains=search_text)

    # STATUS FILTER
    if status == "active":
        base_query = base_query.filter(status=True)
    elif status == "inactive":
        base_query = base_query.filter(status=False)

    # ORDERING
    status_list = base_query.order_by("-created_at")

    # PAGINATION
    paginator = Paginator(status_list, 10, orphans=1)  # Using consistent PAGE_SIZE
    if not page_number:
        page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    # ASSET COUNT
    status_ids = list(page_object.object_list.values_list("id", flat=True))

    asset_counts = (
        Asset.undeleted_objects.filter(
            organization=request.user.organization, asset_status_id__in=status_ids
        )
        .values("asset_status")
        .annotate(asset_count=Count("id", distinct=True))
    )

    asset_status_asset_count = {
        item["asset_status"]: item["asset_count"] for item in asset_counts
    }

    stats = {
        "total_statuses": total_statuses,
        "active_statuses": active_statuses,
        "inactive_statuses": inactive_statuses,
        "deleted_statuses_count": deleted_statuses_count,
    }

    return page_object, asset_status_asset_count, stats
@transaction.atomic
def add_maintenance_record(request, form, asset):
    record = form.save(commit=False)
    record.asset = asset
    record.organization = request.user.organization
    record.service_id = f"MN-{random.randint(10000, 99999)}"
    record.created_by = str(request.user.id)
    record.save()
    messages.success(request, f"Maintenance record {record.service_id} added successfully.")
    return record


@transaction.atomic
def update_maintenance_record(request, record):
    technician = request.POST.get("technician")
    status = request.POST.get("status")
    if technician and technician != record.technician:
        record.technician = technician
    if status and status != record.status:
        record.status = status
    record.updated_by = str(request.user.id)
    record.save()
    messages.success(request, f"Maintenance record {record.service_id} updated.")
    return record
