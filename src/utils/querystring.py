"""Convenience function to use the querystring templatetag from python."""

from __future__ import annotations

from django.template import RequestContext

from utils.templatetags import querystring


def querystring_from_request(request, **kwargs):
    """Convenience function to use the querystring templatetag from python."""
    context = RequestContext(request)
    return querystring.querystring(context, **kwargs)
