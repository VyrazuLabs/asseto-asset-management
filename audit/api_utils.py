from .utils import next_audit_due,next_audit_due_for_asset
from .models import Audit,AuditImage
from assets.models import Asset
from datetime import datetime
from dateutil.relativedelta import relativedelta

def next_audit_due(audit_id):
    audit=Audit.objects.filter(id=audit_id).first()
    interval_days = audit.asset.product.get_audit_interval()
    today=datetime.today().date()
    if not interval_days:
        return None
    # last_audit = audits.asset.order_by("-created_at").first()
    if not audit:
        base_date = audit.created_at.date()
    else:
        base_date = audit.created_at.date()
 
    # First due date after interval
    next_due = base_date + relativedelta(days=interval_days)
    return  next_due

def audit_image_url(audit):
    if audit:
        get_audit_image = (
            AuditImage.objects.filter(
                audit=audit,
            )
            .order_by('-uploaded_at')
            .first()
        )
        if get_audit_image:
            return get_audit_image.image.url
        else:
            return ""
    return ""

def get_completed_audits(request,audit_queryset):
    obj=[]
    for it in audit_queryset:
        dict={
        'id':it.id,
        'asset_name':it.asset.name,
        'asset_tag':it.asset.tag,
        'audited_by':it.audited_by.dynamic_display_name(request.user.full_name),
        'condition':it.condition_label(),
        'created_at':it.created_at,
        'notes':it.notes,
        'next_audit_date':next_audit_due(it.id),
        'assigned_to':it.assigned_to,
        'audit_image_url':audit_image_url(it),
        }
        obj.append(dict)
    print("OBJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ",obj)
    return obj

def get_pending_audits(request):
    asset_list = Asset.undeleted_objects.all()
    obj=[]
    for asset in asset_list:
        has_audit = Audit.objects.filter(asset=asset).order_by('-created_at').first()
        next_due_date = next_audit_due_for_asset(asset)
        if has_audit:
            if (next_due_date > datetime.now().date()):
                continue
        dict = {
        "asset" : asset.name,
        "expected_audit_date": next_due_date,
        "last_audit_date": has_audit.last_audit_date.created_at.date if has_audit else None
        }
        obj.append(dict)
    return obj

def audit_data_by_id(request,id):
    audit=Audit.objects.filter(id=id).first()
    dict={
        'id':audit.id,
        'asset_name':audit.asset.name,
        'asset_tag':audit.asset.tag,
        'audited_by':audit.audited_by.dynamic_display_name(request.user.full_name),
        'condition':audit.condition_label(),
        'created_at':audit.created_at,
        'notes':audit.notes,
        'next_audit_date':next_audit_due(id),
        'assigned_to':audit.assigned_to,
        'audit_image_url':audit_image_url(audit),
    }
    print("dict",dict)
    return dict

def get_audit_details(request,id):
    audit = Audit.objects.filter(id=id).first()
    images=AuditImage.objects.filter(audit=audit)
    image_list=[image.image.url for image in images]
    print("IMAGE LIST",image_list)
    data = {
        "asset_tag": audit.asset.tag,
        "condition": audit.condition_label(),
        "notes": audit.notes,
        "assigned_to": audit.assigned_to,
        "audited_by": audit.audited_by.full_name if audit.audited_by else None,
        "created_at": audit.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "image_list":image_list
    }
    return data