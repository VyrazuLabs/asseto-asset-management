from datetime import datetime, timedelta,timezone

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

AUDIT_INTERVAL_VALUE = {
    0: None,   # Not Applicable
    1: 12,     # Yearly
    2: 6,      # Half-Yearly
    3: 3,      # Quarterly
    4: 2,      # Bi Monthly
    5: 1,      # Monthly
}

def next_audit_due(asset):
    """
    Returns the next audit due date based on:
        - last audit date
        - audit interval
        - deadline rollover rule (30-day grace)

    Supports: monthly, bi-monthly, quarterly, half-yearly, yearly.
    """

    interval_months = AUDIT_INTERVAL_VALUE.get(asset.get_audit_interval())
    if not interval_months:
        return None  # Not applicable

    # Get last audit
    last_audit = asset.audits.order_by("-created_at").first()

    # If never audited → due date is from asset creation date
    if not last_audit:
        base_date = asset.created_at.date()
    else:
        base_date = last_audit.created_at.date()

    # First due date after interval
    next_due = base_date + relativedelta(months=interval_months)

    # Grace period rule: If 30 days pass after due date → push to next interval
    today = datetime.today().date()

    if today > next_due + timedelta(days=30):
        # Carry over to next period
        # Calculate how many cycles have passed
        months_passed = (today.year - next_due.year) * 12 + (today.month - next_due.month)
        cycles = (months_passed // interval_months) + 1
        next_due = next_due + relativedelta(months=interval_months * cycles)

    return next_due


# def get_condition_type(index):
