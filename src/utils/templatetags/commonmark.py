import commonmark, bleach

from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def trustedcommonmark(value):
    """Returns HTML given some commonmark Markdown. Also allows real HTML, so do not use this with untrusted input."""
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    ast = parser.parse(value)
    return mark_safe(renderer.render(ast))

@register.filter
@stringfilter
def untrustedcommonmark(value):
    """Returns HTML given some commonmark Markdown. Cleans actual HTML from input using bleach, suitable for use with untrusted input."""
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    ast = parser.parse(bleach.clean(value))
    return mark_safe(renderer.render(ast))

