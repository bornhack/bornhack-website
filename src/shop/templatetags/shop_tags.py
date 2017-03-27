from django import template
from django.utils.safestring import mark_safe
from decimal import Decimal

register = template.Library()


@register.filter
def currency(value):
    try:
        return "{0:.2f} DKK".format(Decimal(value))
    except ValueError:
        return False


@register.filter
def approxeur(value):
    try:
        return "{0:.2f} EUR".format(value / Decimal(7.5))
    except ValueError:
        return False


@register.filter()
def truefalseicon(value):
    if value:
        return mark_safe("<span class='text-success glyphicon glyphicon-ok'></span>")
    else:
        return mark_safe("<span class='text-danger glyphicon glyphicon-remove'></span>")

