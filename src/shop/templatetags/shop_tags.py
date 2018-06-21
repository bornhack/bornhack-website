from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def currency(value):
    try:
        return "{0:.2f} DKK".format(Decimal(value))
    except ValueError:
        return False

