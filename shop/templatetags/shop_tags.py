from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def currency(value):
    return "{0:.2f} DKK".format(value)


@register.filter()
def truefalseicon(value):
    if value:
        return mark_safe("<span class='text-success glyphicon glyphicon-th-ok'></span>")
    else:
        return mark_safe("<span class='text-success glyphicon glyphicon-th-remove'></span>")

