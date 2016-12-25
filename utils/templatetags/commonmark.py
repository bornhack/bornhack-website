import CommonMark, bleach

from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def commonmark(value):
    """Returns HTML given some CommonMark Markdown. Does not clean HTML, not for use with untrusted input."""
    parser = CommonMark.Parser()
    renderer = CommonMark.HtmlRenderer()
    ast = parser.parse(value)
    return mark_safe(renderer.render(ast))

@register.filter
@stringfilter
def unsafecommonmark(value):
    """Returns HTML given some CommonMark Markdown. Cleans HTML from input using bleach, suitable for use with untrusted input."""
    parser = CommonMark.Parser()
    renderer = CommonMark.HtmlRenderer()
    ast = parser.parse(bleach.clean(value))
    return mark_safe(renderer.render(ast))

