import CommonMark

from django import template
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True)
def commonmark(value):
    parser = CommonMark.Parser()
    renderer = CommonMark.HtmlRenderer()
    ast = parser.parse(force_text(value))
    return mark_safe(
        force_text(renderer.render(ast))
    )