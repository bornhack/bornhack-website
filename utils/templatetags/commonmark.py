import CommonMark

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def commonmark(value):
    parser = CommonMark.Parser()
    renderer = CommonMark.HtmlRenderer()
    ast = parser.parse(value)
    return renderer.render(ast)

