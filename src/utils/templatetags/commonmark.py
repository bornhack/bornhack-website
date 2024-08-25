import bleach
import commonmark
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import SafeString
from django.utils.safestring import mark_safe

register = template.Library()


def parse_commonmark(value: str) -> str:
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    ast = parser.parse(value)
    return renderer.render(ast)


@register.filter(is_safe=True)
@stringfilter
def trustedcommonmark(value: str) -> SafeString:
    """Returns HTML given some (trusted) commonmark Markdown.

    Also allows real HTML, so do not use this with untrusted input."""
    markdown = parse_commonmark(value)
    result = bleach.linkify(markdown, parse_email=True)
    return mark_safe(result)  # noqa: S308


@register.filter(is_safe=True)
@stringfilter
def untrustedcommonmark(value: str) -> SafeString:
    """Returns HTML given some (untrusted) commonmark Markdown.

    Cleans actual HTML from input using bleach, suitable for use with untrusted input."""
    cleaned = bleach.clean(value)
    markdown = parse_commonmark(cleaned)
    result = bleach.linkify(markdown, parse_email=True)
    return mark_safe(result)  # noqa: S308
