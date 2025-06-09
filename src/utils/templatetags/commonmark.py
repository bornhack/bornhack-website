from __future__ import annotations

import commonmark
import nh3
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

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
    markdown = parse_commonmark(value)
    return mark_safe(markdown)


@register.filter(is_safe=True)
@stringfilter
def untrustedcommonmark(value):
    """Returns HTML given some commonmark Markdown. Cleans actual HTML from input using nh3, suitable for use with untrusted input."""
    cleaned = nh3.clean(value, tags=set())
    markdown = parse_commonmark(cleaned)
    return mark_safe(markdown)
