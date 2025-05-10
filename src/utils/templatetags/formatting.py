import json
from django import template

register = template.Library()


@register.filter(name="format_json")
def format_json(value):
    try:
        return json.dumps(value, indent=2)
    except ValueError:
        return value
