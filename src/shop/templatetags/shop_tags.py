from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def currency(value):
    try:
        return "{0:.2f} DKK".format(Decimal(value))
    except ValueError:
        return False
