from django import template
from dateutil.parser import parse
from configurations.utils import get_currency_and_datetime_format
from datetime import datetime
from configurations.models import LocalizationConfiguration
from configurations.constants import NAME_FORMATS
from audit.utils import get_time_difference
from audit.constants import AUDIT_INTERVAL_VALUE
from datetime import datetime, timedelta,timezone
from dateutil.relativedelta import relativedelta

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_at_index(list_obj, index):
        try:
            return list_obj[index]
        except (IndexError, TypeError):
            return None
        
@register.filter
def split(value, key=' '):
    return value.split(key)

@register.simple_tag(takes_context=True)
def format_datetime(context,x):
    request = context['request']
    obj=get_currency_and_datetime_format(request.user.organization)
    if obj and obj['date_format']:
        output_format=obj['date_format']
    else:
        output_format='DD-MM-YYYY'
    """Convert datetime object to the specified output format."""
    # x = datetime.datetime.now()
    if isinstance(x, str):
        x = parse(x)

    formats = {
        'YYYY-MM-DD': '%Y-%m-%d',
        'Day Month DD, Year': '%A %B %d, %Y',   
        'Month DD, YYYY': '%B %d, %Y',
        'DD/MM/YYYY': '%d/%m/%Y',
        'MM/DD/YYYY': '%m/%d/%Y'
    }

    if output_format not in formats:
        raise ValueError("Invalid format. Choose from: " + ", ".join(formats.keys()))

    return x.strftime(formats[output_format])
@register.simple_tag(takes_context=True)
def dynamic_display_name(context,fullname):
    request = context['request']
    format_key= LocalizationConfiguration.objects.filter(organization=request.user.organization).first()
    # for id,it in NAME_FORMATS.items():
    #     if format_key and format_key.name_display_format == id:
    #         format_key=id
    format_key=format_key.name_display_format if format_key else "0"
    """
    Formats a full name string according to the specified naming convention.
    
    Args:
        fullname (str): The full name (e.g., "John Doe")
        format_key (str): Key selecting the name format
    
    Returns:
        str: Formatted name string
    """
    parts = (fullname or "").strip().split()
    first = parts[0] if len(parts) >= 1 else ""
    last = parts[-1] if len(parts) >= 2 else ""
    first_initial = first[0] if first else ""
    context = {
        "first": first,
        "last": last,
        "first_initial": first_initial,
    }
    format_key=str(format_key)
    fmt = NAME_FORMATS.get(format_key)

    try:
        return fmt.format(**context).strip()
    except Exception:
        # fallback to standard "First Last"
        return f"{first} {last}".strip()


@register.filter
def audit_time_diff(audit):
    # Guard clauses if related objects are missing
    if not audit or not audit.asset or not audit.asset.created_at or not audit.asset.product:
        return None
    
    asset_creation_time = audit.asset.created_at
    audit_interval_days = audit.asset.product.audit_interval
    
    return get_time_difference(asset_creation_time, audit_interval_days)

@register.filter
def next_audit_due(audit):
    print(audit.asset.product.name,"audit in filter")
    interval_days = audit.asset.product.get_audit_interval()
    print(interval_days,"interval date")
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

    # Grace period rule: If 30 days pass after due date → push to next interval
    days_remaining = (next_due - today).days
    print("days remaining",days_remaining)
    return  days_remaining
    # else:
    #     days_remaining = (next_due - today).days
    #     return days_remaining

