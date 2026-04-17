from datetime import datetime, timedelta,timezone
from .constants import AUDIT_INTERVAL_VALUE
from dateutil.relativedelta import relativedelta
from .models import Audit
from assets.models import Asset
from django.core.paginator import Paginator

def get_audit_stats(request):
    """Return stat card counts for the audit list pages."""
    thirty_days_ago = datetime.now() - timedelta(days=30)
    completed_count = Audit.objects.filter(created_at__gte=thirty_days_ago).count()
    total_audit_count = Audit.objects.count()

    # Pending: assets whose next audit is overdue or never audited
    asset_list = Asset.undeleted_objects.all()
    pending_count = 0
    for asset in asset_list:
        has_audit = Audit.objects.filter(asset=asset).order_by('-created_at').first()
        next_due = next_audit_due_for_asset(asset)
        if has_audit and next_due:
            if next_due <= datetime.now().date():
                pending_count += 1
        elif not has_audit:
            pending_count += 1

    return {
        'total_audit_count': total_audit_count,
        'completed_count': completed_count,
        'pending_count': pending_count,
    }


def get_completed_audit(request):
    thirty_days_ago = datetime.now() - timedelta(days=30)

    audits = Audit.objects.filter(
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')

    page = request.GET.get('page', 1)
    paginator = Paginator(audits, 10)
    audits_page = paginator.get_page(page)
    
    from assets.models import AssetImage, AssignAsset
    from collections import defaultdict
    asset_ids = [audit.asset.id for audit in audits if audit.asset]
    
    asset_images = {}
    for img in AssetImage.objects.filter(asset__organization=request.user.organization, asset_id__in=asset_ids).order_by('-uploaded_at'):
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img

    asset_user_map = {}
    for assign in AssignAsset.objects.select_related('user').filter(asset_id__in=asset_ids).order_by('-assigned_date'):
        if assign.asset_id not in asset_user_map:
            asset_user_map[assign.asset_id] = None
        if assign.user:
            asset_user_map[assign.asset_id] = {"full_name": assign.user.full_name, "image": assign.user.profile_pic}

    asset_conditions_map = defaultdict(list)
    for a in Audit.objects.filter(asset_id__in=asset_ids).order_by('created_at'):
        asset_conditions_map[a.asset_id].append(a.condition)

    audits_page.asset_images = asset_images
    audits_page.asset_user_map = asset_user_map
    audits_page.asset_conditions_map = asset_conditions_map

    return audits_page

def get_pending_audits(request):
    asset_list = Asset.undeleted_objects.all()
    data_set = []
    for asset in asset_list:
        # latest_audit = Audit.objects.filter(
        #     asset=OuterRef("pk")
        # ).order_by("-created_at")

        # assets = Asset.objects.annotate(
        #     last_audit_date=Subquery(latest_audit.values("created_at")[:1])
        # )   
        has_audit = Audit.objects.filter(asset=asset).order_by('-created_at').first()
        next_due_date = next_audit_due_for_asset(asset)
        if has_audit and next_due_date:
            if (next_due_date > datetime.now().date()):
                continue
        data = {}
        data["asset"] = asset
        data["expected_audit_date"] = next_due_date
        data["last_audit_date"] = has_audit
        data_set.append(data)

    from assets.models import AssetImage, AssignAsset
    from collections import defaultdict
    
    asset_ids = [data['asset'].id for data in data_set if data.get('asset')]
    
    asset_images = {}
    for img in AssetImage.objects.filter(asset__organization=request.user.organization, asset_id__in=asset_ids).order_by('-uploaded_at'):
        if img.asset_id not in asset_images:
            asset_images[img.asset_id] = img

    asset_user_map = {}
    for assign in AssignAsset.objects.select_related('user').filter(asset_id__in=asset_ids).order_by('-assigned_date'):
        if assign.asset_id not in asset_user_map:
            asset_user_map[assign.asset_id] = None
        if assign.user:
            asset_user_map[assign.asset_id] = {"full_name": assign.user.full_name, "image": assign.user.profile_pic}

    asset_conditions_map = defaultdict(list)
    for a in Audit.objects.filter(asset_id__in=asset_ids).order_by('created_at'):
        asset_conditions_map[a.asset_id].append(a.condition)

    return {
        'data_set': data_set,
        'asset_images': asset_images,
        'asset_user_map': asset_user_map,
        'asset_conditions_map': asset_conditions_map
    }

def get_time_difference(asset_creation_time, audit_interval_days):
    if asset_creation_time.tzinfo is not None and asset_creation_time.tzinfo.utcoffset(asset_creation_time) is not None:
        asset_creation_time = asset_creation_time.astimezone(timezone.utc).replace(tzinfo=None)
    
    now = datetime.now()
    audit_due_date = asset_creation_time + timedelta(days=audit_interval_days)
    time_diff = audit_due_date - now
    return time_diff.days
# product = Product.objects.get(id=some_id)
# time_left = get_time_difference(product.created_at, product.audit_interval)
# if time_left.total_seconds() < 0:
#     print("Audit is overdue by", abs(time_left))
# else:
#     print("Time left until audit:", time_left)
def audit_time_diff(audit):
    # Guard clauses if related objects are missing
    if not audit or not audit.asset or not audit.created_at or not audit.asset.product:
        return None
    
    asset_creation_or_updation_time = audit.created_at
    audit_interval_days = audit.asset.product.get_audit_interval()
    return get_time_difference(asset_creation_or_updation_time, audit_interval_days)
def is_pending_audit(audit):
    time_diff = audit_time_diff(audit)
    if time_diff is None:
        return False  # or handle missing data
    if time_diff < 0:
        return time_diff
    else :
        return 0
def is_upcoming_audit(audit):
    time_diff = audit_time_diff(audit)
    if time_diff is None:
        return 0
    return time_diff >= 0


def next_audit_due(audit=None, asset=None):
    if audit:
        if not audit or not audit.asset or not audit.asset.product:
            return None, False

        interval_days = audit.asset.product.get_audit_interval()
        if not interval_days or interval_days == 0:
            return None, False

        today = datetime.today().date()
        last_audit_date = audit.created_at.date()
        next_due = last_audit_date + relativedelta(days=interval_days)

        days_remaining = (next_due - today).days

        is_pending = days_remaining < 0

    # def get_condition_type(index):
        return days_remaining, is_pending

    elif asset:
        if not asset or not asset.product:
            return None, False

        interval_days = asset.product.get_audit_interval()
        if not interval_days or interval_days == 0:
            return None, False

        today = datetime.today().date()
        asset_creation_date = asset.created_at.date()
        next_due = asset_creation_date + relativedelta(days=interval_days)

        days_remaining = (next_due - today).days

        is_pending = days_remaining < 0

        return days_remaining, is_pending





def next_audit_due_for_asset(asset):
    interval_days = asset.product.get_audit_interval()
    if interval_days == 0:
        return None

    audit_asset = Audit.objects.filter(asset=asset).order_by("-created_at").first()
    base_date = asset.created_at.date() if not audit_asset else audit_asset.created_at.date()
    next_due = base_date + relativedelta(days=interval_days)
    return  next_due

def next_audit_due(audit):
    if not audit or not audit.asset or not audit.asset.product:
        return None, False

    interval_days = audit.asset.product.get_audit_interval()
    if not interval_days or interval_days == 0:
        return None, False

    today = datetime.today().date()
    last_audit_date = audit.created_at.date()
    next_due = last_audit_date + relativedelta(days=interval_days)

    days_remaining = (next_due - today).days

    is_pending = days_remaining < 0

# def get_condition_type(index):
    return days_remaining, is_pending

def get_tag_list(tag):
    tags = Asset.undeleted_objects.filter(tag__icontains=tag)
    arr=[]
    for t in tags:
        arr.append(t.tag)
    return arr