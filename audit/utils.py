from datetime import datetime, timedelta,timezone
from .constants import AUDIT_INTERVAL_VALUE

def get_time_difference(asset_creation_time, audit_interval_days):
    if asset_creation_time.tzinfo is not None and asset_creation_time.tzinfo.utcoffset(asset_creation_time) is not None:
        asset_creation_time = asset_creation_time.astimezone(timezone.utc).replace(tzinfo=None)
    
    now = datetime.now()
    audit_due_date = asset_creation_time + timedelta(days=audit_interval_days)
    time_diff = audit_due_date - now
    # print("time diff", abs(time_diff.days))
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
    print("asset_creation_time", audit_interval_days)
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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta



# def next_audit_due(audit):
#     interval_days = audit.asset.product.get_audit_interval()
#     print(interval_days,"interval date")
#     today=datetime.today().date()
#     if not interval_days:
#         return None 
#     # last_audit = audits.asset.order_by("-created_at").first()

#     if not audit:
#         base_date = audit.created_at.date()
#     else:
#         base_date = audit.created_at.date()

#     # First due date after interval
#     next_due = base_date + relativedelta(days=interval_days)

#     # Grace period rule: If 30 days pass after due date → push to next interval
#     days_remaining = (next_due - today).days
#     print("days remaining",days_remaining)
#     return  days_remaining
#     # else:

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

    return days_remaining, is_pending
    # return days_remaining
