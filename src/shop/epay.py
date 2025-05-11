from __future__ import annotations

import hashlib

from django.conf import settings


def calculate_epay_hash(order, request):
    hashstring = (
        f"{settings.EPAY_MERCHANT_NUMBER}{order.description}11{order.total * 100}DKK"
        f"{order.pk}{order.get_epay_accept_url(request)}{order.get_cancel_url(request)}{order.get_epay_callback_url(request)}{settings.EPAY_MD5_SECRET}"
    )
    epay_hash = hashlib.md5(hashstring.encode("utf-8")).hexdigest()
    return epay_hash


def validate_epay_callback(query):
    hashstring = ""
    for key, value in query.items():
        if key != "hash":
            hashstring += value
    hash = hashlib.md5(
        (hashstring + settings.EPAY_MD5_SECRET).encode("utf-8"),
    ).hexdigest()
    return hash == query["hash"]
