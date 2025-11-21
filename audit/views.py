from django.shortcuts import render,redirect,get_object_or_404
from .models import Audit
from assets.models import AssetImage
from .forms import AuditForm
from django.core.paginator import Paginator
from assets.models import AssignAsset,Asset
from authentication.models import User
from audit.utils import next_audit_due, next_audit_due_for_asset
from datetime import datetime,timedelta,timezone 
from django.http import JsonResponse
from audit.models import AuditImage
from django.db.models import OuterRef, Subquery

PAGE_SIZE = 10
ORPHANS = 1

def add_audit(request):
    id = request.GET.get('id', None)
    get_audit = Audit.objects.filter(id=id).first() if id else None
    condition=request.POST.get('condition',None)
    comments=request.POST.get('comments',None)
    assigned_to=request.POST.get('assigned-to',None)
    tag=request.POST.get('tag',None)
    get_asset=Asset.objects.filter(tag=tag).first()
    
    if request.method == 'POST':
        errors={}
        if not condition:
            errors["condition"] = "Condition is required."

        if not comments:
            errors["comments"] = "Comments cannot be empty."


        # If ANY custom errors exist → return template with errors
        if errors:
            return render(request, "audit/add_audit.html", {
                "errors": errors,
                "get_audit": get_audit,
                "tag": tag,
                "comments": comments,
                "assigned_users": User.undeleted_objects.all()
            })
        form = AuditForm(request.POST, request.FILES, organization=request.user.organization)
        # image_form = AssetImageForm(request.POST, request.FILES)
        image_instance=None
        files=request.FILES.getlist('image')
        if not files:
            file = request.FILES.get("image")
            if file:
                files = [file]
        for f in files:
            AuditImage.objects.create(asset=get_audit, image=f)
        Audit.objects.create(
            asset=get_asset,
            assigned_to=assigned_to,
            condition= condition,
            notes= comments,
            audited_by=request.user if request.user.is_authenticated else None,
            created_at= datetime.now(),
            organization=request.user.organization,
        )
        return redirect('audit:completed_audits')

    elif request.method == 'GET':
        user_list = [assign for assign in User.undeleted_objects.all() if assign is not None]
        context = {'get_audit': get_audit, 'assigned_users': user_list}
        return render(request, 'audit/add_audit.html', context)


def get_audits_by_id(request, id):
    # Get the audit id
    get_asset = get_object_or_404(Asset, id=id)
    get_audit=Audit.objects.filter(asset__id=id).order_by('-created_at').first()
    get_assigned_user = AssignAsset.objects.filter(asset__id=id).first()
    if request.method == 'POST':
        errors={}
        comments = request.POST.get('comments', None)
        condition = request.POST.get('condition', None)
        if not condition:
            errors["condition"] = "Condition is required."

        if not comments:
            errors["comments"] = "Comments cannot be empty."


        # If ANY custom errors exist → return template with errors
        if errors:
            return render(request, "audit/add_audit.html", {
                "errors": errors,
                "comments": comments,
                "assigned_users": User.undeleted_objects.all()
            })
        files=request.FILES.getlist('image')
        if not files:
            file = request.FILES.get("image")
            if file:
                files = [file]
        created_audit=Audit.objects.create(
            asset=get_asset,
            assigned_to=get_assigned_user.user.full_name if get_assigned_user else '',
            condition= condition,
            notes= comments,
            audited_by=request.user if request.user.is_authenticated else None,
            created_at= datetime.now(),
            organization=request.user.organization,
        )
        for f in files:
                AuditImage.objects.create(audit=created_audit, image=f)
        return redirect('audit:completed_audits')

    elif request.method == 'GET':
        if get_assigned_user is None:
            user_list = list(User.undeleted_objects.all())
            context = {'get_asset': get_asset, 'assigned_users': user_list}
        else:
            context = {'get_asset': get_asset, 'asset_assigned_users': get_assigned_user.user.full_name}
        return render(request, 'audit/add_audit.html', context)

def audit_list(request):
    audits = Audit.objects.all()
    return render(request, 'audit/audit_list.html',context={
        'audits': audits
    })


def asset_audit_history(request,id):
    audit_list = Audit.objects.filter(asset__id=id).order_by('-created_at')
    paginator = Paginator(audit_list, PAGE_SIZE, orphans=ORPHANS)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    context = {
        'sidebar': 'assets',
        'submenu': 'assigned-assets',
        'page_object': page_object,
        'title': 'Assigned Assets'
    }
    return render(request, 'audit/asset-audit-history.html', context=context)

def completed_audits(request):
    thirty_days_ago = datetime.now() - timedelta(days=30)
    audits = Audit.objects.filter(
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')
    return render(request, 'audit/audit_list.html', {
        'audits': audits
    })

def pending_audits(request):
    asset_list = Asset.undeleted_objects.all()
    data_set = []
    for asset in asset_list:
        has_audit = Audit.objects.filter(asset=asset).order_by('-created_at').first()
        next_due_date = next_audit_due_for_asset(asset)
        if has_audit:
            print(next_due_date, datetime.now().date(), next_due_date < datetime.now().date())
            if (next_due_date > datetime.now().date()):
                continue
        data = {}
        data["asset"] = asset
        data["expected_audit_date"] = next_due_date
        data["last_audit_date"] = has_audit
        data_set.append(data)

    return render(request, 'audit/pending_audits.html', {
        'data_set': data_set
    })

    #     latest_audit = Audit.objects.filter(asset=asset).order_by('-created_at').first()
    #     if latest_audit:
    #         days_remaining, is_pending = next_audit_due(latest_audit)
    #         if days_remaining is not None and days_remaining < 0:
    #             asset.latest_audit = latest_audit
    #             asset.expected_date = latest_audit.created_at + timedelta(days=abs(days_remaining))
    #     else:
    #         asset.latest_audit = None
    #         asset.expected_date = None
    # latest_audits=Audit.objects.order_by('-created_at').all()


def get_assigned_user(request, tag=None):
    if not tag:
        return JsonResponse({"error": "No tag provided"}, status=400)

    asset = Asset.objects.filter(tag=tag).first()

    if not asset:
        return JsonResponse({"exists": False, "assigned_user": None}, status=200)

    assign_record = AssignAsset.objects.filter(asset=asset).order_by("-assigned_date").first()

    return JsonResponse({
        "exists": True,
        "assigned_user": assign_record.user.full_name if assign_record else None,
        "assigned_user_id": assign_record.user.id if assign_record else None
    })

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
    images=AuditImage.objects.filter(audit=audit)
    return render(request, 'audit/details.html', context={'audit': audit, 'data': data,'images':images})