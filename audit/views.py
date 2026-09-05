from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from assets.models import Asset, AssignAsset
from audit.models import AuditImage
from audit.utils import get_tag_list
from authentication.models import User
from common.permissions import require_any_permission

from .forms import AuditForm
from .models import Audit
from .utils import get_audit_stats, get_completed_audit, get_pending_audits

PAGE_SIZE = 10
ORPHANS = 1


@login_required
@permission_required("audit.add_audit", raise_exception=True)
def add_audit(request):
    id = request.GET.get("id", None)
    get_audit = Audit.objects.filter(id=id).first() if id else None
    condition = request.POST.get("condition", None)
    comments = request.POST.get("comments", None)
    assigned_to = request.POST.get("assigned-to", None)
    tag = request.POST.get("tag", None)
    get_asset = Asset.objects.filter(tag=tag).first()
    user_list = [
        assign for assign in User.undeleted_objects.all() if assign is not None
    ]
    if request.method == "POST":
        errors = {}
        if not condition:
            errors["condition"] = "Condition is required."

        if not comments:
            errors["comments"] = "Comments cannot be empty."

        # If ANY custom errors exist → return template with errors
        if errors:
            return render(
                request,
                "audit/add_audit.html",
                {
                    "errors": errors,
                    "get_audit": get_audit,
                    "tag": tag,
                    "comments": comments,
                    "assigned_users": User.undeleted_objects.all(),
                },
            )
        form = AuditForm(
            request.POST, request.FILES, organization=request.user.organization
        )
        files = request.FILES.getlist("image")
        if not files:
            file = request.FILES.get("image")
            if file:
                files = [file]
        audit_create = Audit.objects.create(
            asset=get_asset,
            assigned_to=assigned_to,
            condition=condition,
            notes=comments,
            audited_by=request.user if request.user.is_authenticated else None,
            created_at=datetime.now(),
            organization=(
                request.user.organization if request.user.is_authenticated else None
            ),
        )
        if get_audit:
            for f in files:
                AuditImage.objects.create(audit=get_audit, image=f)
        else:
            for f in files:
                AuditImage.objects.create(audit=audit_create, image=f)
        messages.success(request, "Audit added successfully")
        context = {
            "get_audit": get_audit,
            "assigned_users": user_list,
            "sidebar": "audit",
        }
        # return render(request, 'audit/add_audit.html', context)
        return redirect("audit:completed_audits")

    elif request.method == "GET":
        context = {
            "get_audit": get_audit,
            "assigned_users": user_list,
            "sidebar": "audit",
            "title": "New Audit Entry",
        }
        return render(request, "audit/add_audit.html", context)


@require_any_permission("audit.add_audit", "audit.edit_audit")
def get_audits_by_id(request, id):
    # Get the asset and its latest audit record
    get_asset = get_object_or_404(Asset, id=id)
    get_audit = Audit.objects.filter(asset__id=id).order_by("-created_at").first()
    get_assigned_user = AssignAsset.objects.filter(asset__id=id).first()
    audit_images = AuditImage.objects.filter(audit=get_audit) if get_audit else []

    def _render_form(extra=None):
        if get_assigned_user is None:
            context = {
                "get_asset": get_asset,
                "assigned_users": list(User.undeleted_objects.all()),
            }
        else:
            context = {
                "get_asset": get_asset,
                "asset_assigned_users": get_assigned_user.user.full_name,
            }
        context.update(
            {
                "get_audit": get_audit,
                "audit_images": audit_images,
                "sidebar": "audit",
                "title": "Update Audit Entry",
            }
        )
        if extra:
            context.update(extra)
        return render(request, "audit/add_audit.html", context)

    if request.method == "POST":
        errors = {}
        comments = request.POST.get("comments", None)
        condition = request.POST.get("condition", None)
        if not condition:
            errors["condition"] = "Condition is required."

        if not comments:
            errors["comments"] = "Comments cannot be empty."

        # If ANY custom errors exist → return template with errors
        if errors:
            return _render_form(
                {
                    "errors": errors,
                    "comments": comments,
                    "condition": condition,
                    "title": "Update Audit",
                }
            )
        files = request.FILES.getlist("image")
        if not files:
            file = request.FILES.get("image")
            if file:
                files = [file]
        if get_audit:
            # Update the existing audit so condition, notes and images stay in sync
            get_audit.condition = condition
            get_audit.notes = comments
            get_audit.audited_by = (
                request.user if request.user.is_authenticated else None
            )
            get_audit.save()
            audit = get_audit
            messages.success(request, "Audit updated successfully")
        else:
            audit = Audit.objects.create(
                asset=get_asset,
                assigned_to=(
                    get_assigned_user.user.full_name if get_assigned_user else ""
                ),
                condition=condition,
                notes=comments,
                audited_by=request.user if request.user.is_authenticated else None,
                organization=request.user.organization,
            )
            if request.user.is_authenticated:
                audit.created_at = datetime.now()
                audit.save()
            messages.success(request, "Audit added successfully")
        for f in files:
            AuditImage.objects.create(audit=audit, image=f)
        return redirect("audit:details", audit.id)

    return _render_form()


@login_required
@permission_required("audit.view_audit", raise_exception=True)
def audit_list(request):
    audits = Audit.objects.all()
    return render(request, "audit/audit_list.html", context={"audits": audits})


@login_required
@permission_required("audit.view_audit", raise_exception=True)
def asset_audit_history(request, id):
    audit_list = Audit.objects.filter(asset__id=id).order_by("-created_at")
    paginator = Paginator(audit_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    context = {
        "sidebar": "assets",
        "submenu": "assigned-assets",
        "page_object": page_object,
        "title": "Assigned Assets",
    }
    return render(request, "audit/asset-audit-history.html", context=context)


@login_required
@permission_required("audit.view_audit", raise_exception=True)
def completed_audits(request):
    audits_page = get_completed_audit(request)
    stats = get_audit_stats(request)
    context = {
        "audits": audits_page,
        "sidebar": "audit",
        "tab": "completed",
        "title": "Completed Audit List",
    }
    context.update(stats)
    return render(request, "audit/audit_list.html", context)


@login_required
@permission_required("audit.view_audit", raise_exception=True)
def pending_audits(request):
    pending_data = get_pending_audits(request)
    stats = get_audit_stats(request)
    context = {"sidebar": "audit", "tab": "pending", "title": "Pending Audit List"}
    context.update(pending_data)
    context.update(stats)
    return render(request, "audit/pending_audits.html", context)


@login_required
@permission_required("audit.view_audit", raise_exception=True)
def get_assigned_user(request, tag=None):
    if not tag:
        return JsonResponse({"error": "No tag provided"}, status=400)

    asset = Asset.objects.filter(tag=tag).first()

    if not asset:
        return JsonResponse({"exists": False, "assigned_user": None}, status=200)
    assign_record = (
        AssignAsset.objects.select_related("user").filter(asset_id=asset.id).first()
    )
    # assign_record = AssignAsset.objects.filter(asset=asset).order_by("-assigned_date").first()

    return JsonResponse(
        {
            "exists": True,
            "assigned_user": assign_record.user.full_name if assign_record else None,
            "assigned_user_id": assign_record.user.id if assign_record else None,
        }
    )


@login_required
@permission_required("audit.view_audit", raise_exception=True)
def audit_details(request, id=None):
    audit = Audit.objects.filter(id=id).first()
    data = {
        "asset_tag": audit.asset.tag,
        "condition": audit.condition,
        "notes": audit.notes,
        "assigned_to": audit.assigned_to,
        "audited_by": audit.audited_by.full_name if audit.audited_by else None,
        "created_at": audit.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
    images = AuditImage.objects.filter(audit=audit)
    return render(
        request,
        "audit/details.html",
        context={"audit": audit, "data": data, "images": images, "sidebar": "audit"},
    )


@login_required
@permission_required("audit.view_audit", raise_exception=True)
def get_asset_tag_list(request):
    tag = request.GET.get("tag")
    tags = get_tag_list(tag)
    return JsonResponse({"tags": tags})


@login_required
@permission_required("audit.delete_audit", raise_exception=True)
def delete_audit_image(request, id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    image = AuditImage.objects.filter(id=id).first()
    if not image:
        return JsonResponse({"error": "Image not found"}, status=404)
    if request.user.is_authenticated and image.audit.organization_id != request.user.organization_id:
        return JsonResponse({"error": "Permission denied"}, status=403)
    image.image.delete(save=False)
    image.delete()
    return JsonResponse({"success": True})
