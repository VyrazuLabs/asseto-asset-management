from datetime import datetime, timedelta, timezone
from .constants import AUDIT_INTERVAL_VALUE
from dateutil.relativedelta import relativedelta
from .models import Audit
from assets.models import Asset, AssignAsset
from django.core.paginator import Paginator
from django.db.models import Q, F, OuterRef, Subquery

AUDIT_INTERVAL_DAYS = dict(AUDIT_INTERVAL_VALUE)


def _asset_audit_schedule(org):
    latest_audit_at = Subquery(
        Audit.objects.filter(asset_id=OuterRef("pk"))
        .order_by("-created_at")
        .values("created_at")[:1]
    )
    return (
        Asset.undeleted_objects.filter(organization=org)
        .annotate(latest_audit_at=latest_audit_at)
        .values("id", "created_at", "product__audit_interval", "latest_audit_at")
    )


def _next_due_from_row(row):
    interval_days = AUDIT_INTERVAL_DAYS.get(row["product__audit_interval"], 0)
    if not interval_days:
        return None
    base_date = row["latest_audit_at"] or row["created_at"]
    return base_date.date() + relativedelta(days=interval_days)


def latest_audit_map(asset_ids):
    """Map asset_id -> newest Audit for that asset.

    One SQL query (Subquery/OuterRef, same pattern as `first_image_map`)
    instead of one `Audit.objects.filter(asset=...).first()` per asset.
    """
    asset_ids = list(asset_ids)
    if not asset_ids:
        return {}
    newest = Audit.objects.filter(asset_id=OuterRef("asset_id")).order_by(
        "-created_at"
    )
    rows = Audit.objects.filter(asset_id__in=asset_ids).annotate(
        newest_pk=Subquery(newest.values("pk")[:1])
    ).filter(pk=F("newest_pk"))
    return {audit.asset_id: audit for audit in rows}


def get_audit_stats(request):
    """Return stat card counts for the audit list pages."""
    org = request.user.organization
    thirty_days_ago = datetime.now() - timedelta(days=30)
    completed_count = Audit.objects.filter(
        Q(organization=org) | Q(organization__isnull=True, asset__organization=org),
        created_at__gte=thirty_days_ago,
    ).count()
    total_audit_count = Audit.objects.filter(
        Q(organization=org) | Q(organization__isnull=True, asset__organization=org)
    ).count()

    today = datetime.now().date()
    pending_count = 0
    for row in _asset_audit_schedule(org).iterator():
        next_due = _next_due_from_row(row)
        if next_due is not None and next_due <= today:
            pending_count += 1

    return {
        "total_audit_count": total_audit_count,
        "completed_count": completed_count,
        "pending_count": pending_count,
    }


def get_completed_audit(request):
    org = request.user.organization
    thirty_days_ago = datetime.now() - timedelta(days=30)

    audits = Audit.objects.filter(
        Q(organization=org) | Q(organization__isnull=True, asset__organization=org),
        created_at__gte=thirty_days_ago,
    ).order_by("-created_at")

    page = request.GET.get("page", 1)
    paginator = Paginator(audits, 10)
    audits_page = paginator.get_page(page)

    from assets.models import AssignAsset
    from collections import defaultdict
    from assets.utils import first_image_map

    # Scoped to the current page: the images, assignments and conditions below
    # are only ever rendered for these rows, not for every audit in the window.
    asset_ids = [
        audit.asset.id for audit in audits_page if audit.asset
    ]

    asset_images = first_image_map(asset_ids)

    asset_user_map = {}
    for assign in (
        AssignAsset.objects.select_related("user")
        .filter(asset_id__in=asset_ids, asset__organization=org)
        .order_by("-assigned_date")
    ):
        if assign.asset_id not in asset_user_map:
            asset_user_map[assign.asset_id] = None
        if assign.user:
            asset_user_map[assign.asset_id] = {
                "full_name": assign.user.full_name,
                "image": assign.user.profile_pic,
            }

    asset_conditions_map = defaultdict(list)
    for a in Audit.objects.filter(asset_id__in=asset_ids).order_by("created_at"):
        asset_conditions_map[a.asset_id].append(a.condition)

    audits_page.asset_images = asset_images
    audits_page.asset_user_map = asset_user_map
    audits_page.asset_conditions_map = asset_conditions_map

    return audits_page


def get_pending_audits(request):
    org = request.user.organization
    today = datetime.now().date()
    pending = []
    for row in _asset_audit_schedule(org).iterator():
        next_due = _next_due_from_row(row)
        if next_due is not None and next_due <= today:
            pending.append({"id": row["id"], "expected_audit_date": next_due})

    page = request.GET.get("page", 1)
    paginator = Paginator(pending, 10)
    page_object = paginator.get_page(page)
    asset_ids = [row["id"] for row in page_object]

    from assets.utils import first_image_map
    from assets.models import AssignAsset
    from collections import defaultdict

    assets = Asset.undeleted_objects.filter(id__in=asset_ids).select_related(
        "product__product_type", "asset_status"
    )
    asset_map = {asset.id: asset for asset in assets}
    latest_audits = latest_audit_map(asset_ids)
    page_object.object_list = [
        {
            "asset": asset_map[row["id"]],
            "expected_audit_date": row["expected_audit_date"],
            "last_audit_date": latest_audits.get(row["id"]),
        }
        for row in page_object
        if row["id"] in asset_map
    ]

    asset_images = first_image_map(asset_ids)

    asset_user_map = {}
    for assign in (
        AssignAsset.objects.select_related("user")
        .filter(asset_id__in=asset_ids, asset__organization=org)
        .order_by("-assigned_date")
    ):
        if assign.asset_id not in asset_user_map:
            asset_user_map[assign.asset_id] = None
        if assign.user:
            asset_user_map[assign.asset_id] = {
                "full_name": assign.user.full_name,
                "image": assign.user.profile_pic,
            }

    asset_conditions_map = defaultdict(list)
    for a in Audit.objects.filter(asset_id__in=asset_ids).order_by("created_at"):
        asset_conditions_map[a.asset_id].append(a.condition)

    return {
        "data_set": page_object,
        "asset_images": asset_images,
        "asset_user_map": asset_user_map,
        "asset_conditions_map": asset_conditions_map,
    }


def get_time_difference(asset_creation_time, audit_interval_days):
    if (
        asset_creation_time.tzinfo is not None
        and asset_creation_time.tzinfo.utcoffset(asset_creation_time) is not None
    ):
        asset_creation_time = asset_creation_time.astimezone(timezone.utc).replace(
            tzinfo=None
        )

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
    else:
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


_UNSET = object()


def next_audit_due_for_asset(asset, last_audit=_UNSET):
    """Next audit due date for `asset`.

    `last_audit` may be passed when the caller already loaded the asset's
    newest audit (or None if it has none) — batched callers use this to avoid
    a query per asset. When omitted, the audit is fetched here.
    """
    if not asset or not asset.product:
        return None
    interval_days = asset.product.get_audit_interval()
    if interval_days == 0:
        return None

    if last_audit is _UNSET:
        last_audit = Audit.objects.filter(asset=asset).order_by("-created_at").first()
    base_date = asset.created_at.date() if not last_audit else last_audit.created_at.date()
    next_due = base_date + relativedelta(days=interval_days)
    return next_due


def get_tag_list(tag):
    assets = list(
        Asset.undeleted_objects.filter(
            Q(tag__icontains=tag) | Q(name__icontains=tag)
        )[:10]
    )
    from assets.utils import first_image_map
    latest_images = first_image_map([a.id for a in assets])
    arr = []
    for asset in assets:
        img = latest_images.get(asset.id)
        arr.append(
            {
                "tag": asset.tag,
                "name": asset.name,
                "image": img.image.url if img and img.image else None,
            }
        )
    return arr
