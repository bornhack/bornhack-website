import datetime
from decimal import Decimal

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="zip")
def zip_lists(a, b):
    return zip(a, b)


@register.filter()
def truefalseicon(value):
    """A template filter to show a green checkbox or red x depending on True/False value"""
    if value is True:
        return mark_safe("<i class='fas fa-check text-success'></i>")
    elif value is False:
        return mark_safe("<i class='fas fa-times text-danger'></i>")
    elif value is None:
        return mark_safe("<i class='fas fa-question text-secondary'></i>")
    else:
        return "the truefalseicon template filter doesn't know what to do here"


@register.simple_tag(takes_context=True)
def feedbackqr(context, facility):
    return facility.get_feedback_qr(request=context["request"])


@register.filter(name="sortable")
def datatables_sortable(value):
    """A template filter to convert a value to something which sorts nicely in datatables js."""
    if isinstance(value, datetime.datetime):
        # return unix timestamp and microseconds
        return value.timestamp()
    elif isinstance(value, datetime.date):
        return value.strftime("%Y%m%d")
    else:
        # unsupported type
        return value


@register.simple_tag(takes_context=True)
def thh(context, fieldname, headerstring=None, tooltip=None, htmlclass=None):
    """Return a <th> element with a popper.js tooltip with the help_text for the model field. Requires an object_list in the context."""
    instance = context["object_list"][0]
    if not headerstring:
        headerstring = fieldname.replace("_", " ").title()
    if not tooltip:
        try:
            tooltip = getattr(instance, f"get_{fieldname}_help_text")()
        except AttributeError:
            tooltip = "No get_help_text_method found on object :("
    return mark_safe(
        f"<th data-container='body' data-placement='bottom' data-toggle='tooltip' title='{tooltip}'>{headerstring}</th>",
    )


@register.filter
def currency(value):
    try:
        return mark_safe(f"{Decimal(value):.2f}&nbsp;DKK")
    except ValueError:
        return False
