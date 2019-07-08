from django import template
from django.utils.dateparse import parse_date

register = template.Library()


@register.simple_tag
def get_weekday(year, month, day):
    return parse_date(
        "%(year)s-%(month)s-%(day)s" % {"year": year, "month": month, "day": day}
    ).strftime("%A")
