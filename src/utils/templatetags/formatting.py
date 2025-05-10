import json
from django import template

register = template.Library()


@register.filter(name="format_json")
def format_json(value):
    if isinstance(value, (dict, list, set)):
        try:
            return json.dumps(value, indent=2)
        except Exception:
            return value
    return value
