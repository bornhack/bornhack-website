from decimal import Decimal

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def truefalseicon(value):
    """ A templatetag to show a green checkbox or red x depending on True/False value """
    if value:
        return mark_safe("<span class='text-success glyphicon glyphicon-ok'></span>")
    else:
        return mark_safe("<span class='text-danger glyphicon glyphicon-remove'></span>")
