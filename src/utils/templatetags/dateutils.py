from __future__ import annotations

from django import template
from django.utils.dateparse import parse_date

register = template.Library()


@register.simple_tag
def get_weekday(year, month, day):
    return parse_date(
        f"{year}-{month}-{day}",
    ).strftime("%A")
