from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable

from django import template

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.http import HttpResponse
    from django.views import View

register = template.Library()


def _resolve_app_name(func: View | Callable[[HttpRequest, ...], HttpResponse]) -> str:
    if hasattr(func, "view_class"):
        resolved_appname = func.view_class.__module__.split(".")[0]
    else:
        resolved_appname = func.__module__.split(".")[0]
    return resolved_appname


@register.simple_tag(takes_context=True)
def menubuttonclass(context: dict[str, Any], appname: str) -> str:
    resolved_appname = _resolve_app_name(context["request"].resolver_match.func)

    if appname == resolved_appname:
        return "btn-primary"
    return "btn-default"


@register.simple_tag(takes_context=True)
def menudropdownclass(context: dict[str, Any], appname: str) -> str | None:
    resolved_appname = _resolve_app_name(context["request"].resolver_match.func)

    if appname == resolved_appname:
        return "active"
    return None
