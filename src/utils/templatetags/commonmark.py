import commonmark, bleach
from html5lib.tokenizer import HTMLTokenizer

from django import template
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def trustedcommonmark(value):
    """Returns HTML given some commonmark Markdown. Also allows real HTML, so do not use this with untrusted input."""
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    ast = parser.parse(value)
    return bleach.linkify(renderer.render(ast), skip_pre=True, parse_email=True, tokenizer=HTMLTokenizer)


@register.filter(is_safe=True)
@stringfilter
def untrustedcommonmark(value):
    """Returns HTML given some commonmark Markdown. Cleans actual HTML from input using bleach, suitable for use with untrusted input."""
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    ast = parser.parse(bleach.clean(value))
    return bleach.linkify(renderer.render(ast), skip_pre=True, parse_email=True, tokenizer=HTMLTokenizer)

