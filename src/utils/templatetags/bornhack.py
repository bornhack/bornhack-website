from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="zip")
def zip_lists(a, b):
    return zip(a, b)


@register.filter()
def truefalseicon(value):
    """A templatetag to show a green checkbox or red x depending on True/False value"""
    if value is True:
        return mark_safe("<span class='text-success glyphicon glyphicon-ok'></span>")
    elif value is False:
        return mark_safe("<span class='text-danger glyphicon glyphicon-remove'></span>")
    elif value is None:
        return mark_safe(
            "<span class='text-secondary glyphicon glyphicon-question'></span>"
        )
    else:
        return "what is this"


@register.simple_tag(takes_context=True)
def feedbackqr(context, facility):
    return facility.get_feedback_qr(request=context["request"])
