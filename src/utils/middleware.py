from __future__ import annotations

from typing import TYPE_CHECKING

from django.shortcuts import redirect

if TYPE_CHECKING:
    from django.http import HttpRequest


class RedirectException(Exception):
    """An exception class meant to be used to redirect from places where
    we cannot just return a HTTPResponse directly (like view setup() methods)
    """

    def __init__(self, url) -> None:
        self.url = url


class RedirectExceptionMiddleware:
    """A simple middleware to catch exceptions of type RedirectException
    and redirect to the url
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def process_exception(self, request: HttpRequest, exception):
        if isinstance(exception, RedirectException) and hasattr(exception, "url"):
            return redirect(exception.url)
        return None

    def __call__(self, request: HttpRequest):
        return self.get_response(request)
