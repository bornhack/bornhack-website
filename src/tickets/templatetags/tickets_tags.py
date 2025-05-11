from __future__ import annotations

from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def currency(value):
    try:
        return f"{Decimal(value):.2f} DKK"
    except ValueError:
        return False
