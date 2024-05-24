from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("bma_widget.html", takes_context=True)
def bma(context, uuid, style="embedtest"):
    count = context.get("bma_widget_counter", 0)
    context["bma_widget_counter"] = count + 1
    return {
        "bma_baseurl": settings.BMA_BASEURL,
        "count": count,
        "uuid": uuid,
        "style": style,
    }
