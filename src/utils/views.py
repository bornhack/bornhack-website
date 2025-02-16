"""Views that do not belong in any specific app."""

from django.http import HttpRequest
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import render


def csrfview(request: HttpRequest) -> HttpResponse:
    """This view just returns a csrf token for use in API calls."""
    return HttpResponse(get_token(request))
