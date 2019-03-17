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
    return renderer.render(ast)


@register.filter(is_safe=True)
@stringfilter
def trustedcommonmark(value):
    """Returns HTML given some commonmark Markdown. Also allows real HTML, so do not use this with untrusted input."""
    linkified_value = bleach.linkify(value, parse_email=True)
    result = parse_commonmark(linkified_value)
    return mark_safe(result)


@register.filter(is_safe=True)
@stringfilter
def untrustedcommonmark(value):
    """Returns HTML given some commonmark Markdown. Cleans actual HTML from input using bleach, suitable for use with untrusted input."""
    cleaned = bleach.clean(value)
    markdown = parse_commonmark(cleaned)
    result = bleach.linkify(markdown, parse_email=True)
    return mark_safe(result)
