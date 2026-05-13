from django import template

register = template.Library()

@register.filter(name="css_class")
def css_class(value: str) -> str:
    """Templatetag for mapping a 'label_type' to a css class."""
    map = {
        "sold_out": "text-bg-danger",
        "low_stock": "text-bg-warning",
        "ending_soon": "text-bg-secondary",
        "bundle": "text-bg-info",
    }

    return map.get(value, "text-bg-primary")
