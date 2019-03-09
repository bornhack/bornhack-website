import commonmark
import bleach

from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

register = template.Library()

def parse_commonmark(value):
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    ast = parser.parse(value)
    return mark_safe(renderer.render(ast))


@register.filter(is_safe=True)
@stringfilter
def trustedcommonmark(value):
    """Returns HTML given some commonmark Markdown. Also allows real HTML, so do not use this with untrusted input."""
    linkified_value = bleach.linkify(value, parse_email=True)
    return parse_commonmark(linkified_value)


@register.filter(is_safe=True)
@stringfilter
def untrustedcommonmark(value):
    """Returns HTML given some commonmark Markdown. Cleans actual HTML from input using bleach, suitable for use with untrusted input."""
    linkified_value = bleach.linkify(bleach.clean(value), parse_email=True)
    return parse_commonmark(linkified_value)
