from __future__ import annotations

from django.shortcuts import redirect


class RedirectException(Exception):
    """An exception class meant to be used to redirect from places where
    we cannot just return a HTTPResponse directly (like view setup() methods)
    """

    def __init__(self, url):
        self.url = url


class RedirectExceptionMiddleware:
    """A simple middleware to catch exceptions of type RedirectException
    and redirect to the url
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def process_exception(self, request, exception):
        if isinstance(exception, RedirectException):
            if hasattr(exception, "url"):
                return redirect(exception.url)

    def __call__(self, request):
        response = self.get_response(request)
        return response
