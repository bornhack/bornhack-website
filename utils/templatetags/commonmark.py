import CommonMark, bleach

from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def commonmark(value):
    parser = CommonMark.Parser()
    renderer = CommonMark.HtmlRenderer()
    ast = parser.parse(bleach.clean(value))
    return mark_safe(renderer.render(ast))

