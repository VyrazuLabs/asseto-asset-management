from django import template

register = template.Library()

@register.filter
def get_item(obj, key):
    try:
        return obj.get(key)
    except (AttributeError, TypeError):
        return None

@register.filter
def get_at_index(list_obj, index):
        try:
            return list_obj[index]
        except (IndexError, TypeError):
            return None