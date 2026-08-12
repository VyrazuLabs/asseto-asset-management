from django import template
register = template.Library()

HTML_TYPE_MAP = {
    "text": "text", "integer": "number", "decimal": "number",
    "date": "date", "email": "email",
}

@register.filter
def cf_html_type(field_type):
    return HTML_TYPE_MAP.get(field_type, "text")

@register.filter
def get_cf_value(cf_values_dict, key):
    return (cf_values_dict or {}).get(key, "")

@register.filter
def cf_has_any_value(definitions, cf_values):
    cf_values = cf_values or {}
    return any(cf_values.get(defn.field_key) for defn in definitions)
