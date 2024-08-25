from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from typing import Any

import requests
from django.conf import settings
from vendor.coinify.coinify_api import CoinifyAPI

from .models import CoinifyAPICallback
from .models import CoinifyAPIInvoice
from .models import CoinifyAPIRequest

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(f"bornhack.{__name__}")


def process_coinify_invoice_json(invoicejson, order, request: HttpRequest):
    # create or update the invoice object in our database
    coinifyinvoice, created = CoinifyAPIInvoice.objects.update_or_create(
        coinify_id=invoicejson["id"],
        order=order,
        defaults={"invoicejson": invoicejson},
    )

    # if the order is paid in full call the mark as paid method now
    if invoicejson["state"] == "complete" and not coinifyinvoice.order.paid:
        coinifyinvoice.order.mark_as_paid(request=request)

    return coinifyinvoice


def save_coinify_callback(request: HttpRequest, order):
    # first make a dict with all HTTP_ headers
    headerdict = {}
    for key, value in list(request.META.items()):
        if key[:5] == "HTTP_":
            headerdict[key[5:]] = value

    # now attempt to parse json
    try:
        parsed = json.loads(request.body.decode("utf-8"))
    except Exception:
        parsed = ""

    # save this callback to db
    return CoinifyAPICallback.objects.create(
        headers=headerdict,
        body=request.body,
        payload=parsed,
        order=order,
    )


def coinify_api_request(api_method, order, **kwargs: dict[str, Any]):
    # Initiate coinify API
    coinifyapi = CoinifyAPI(settings.COINIFY_API_KEY, settings.COINIFY_API_SECRET)

    # is this a supported method?
    if not hasattr(coinifyapi, api_method):
        logger.error("coinify api method not supported" % api_method)
        return False

    # get and run the API call using the SDK
    method = getattr(coinifyapi, api_method)

    # catch requests exceptions as described in https://github.com/CoinifySoftware/python-sdk#catching-errors and
    # http://docs.python-requests.org/en/latest/user/quickstart/#errors-and-exceptions
    try:
        response = method(**kwargs)
    except requests.exceptions.RequestException as E:
        logger.error("requests exception during coinify api request: %s" % E)
        return False

    # save this API request to the database
    req = CoinifyAPIRequest.objects.create(
        order=order,
        method=api_method,
        payload=kwargs,
        response=response,
    )
    logger.debug(f"saved coinify api request {req.id} in db")

    return req


def handle_coinify_api_response(apireq, order, request: HttpRequest):
    if apireq.method in ("invoice_create", "invoice_get"):
        # Parse api response
        if apireq.response["success"]:
            # save this new coinify invoice to the DB
            return process_coinify_invoice_json(
                invoicejson=apireq.response["data"],
                order=order,
                request=request,
            )
        else:
            api_error = apireq.response["error"]
            logger.error(
                "coinify API error: {} ({})".format(
                    api_error["message"],
                    api_error["code"],
                ),
            )
            return False
    else:
        logger.error("coinify api method not supported" % apireq.method)
        return False


#################################################################
# API CALLS


def get_coinify_invoice(coinify_invoiceid, order, request: HttpRequest):
    # put args for API request together
    invoicedict = {"invoice_id": coinify_invoiceid}

    # perform the api request
    apireq = coinify_api_request(api_method="invoice_get", order=order, **invoicedict)

    return handle_coinify_api_response(apireq, order, request)


def create_coinify_invoice(order, request: HttpRequest):
    # put args for API request together
    invoicedict = {
        "amount": float(order.total),
        "currency": "DKK",
        "plugin_name": "BornHack webshop",
        "plugin_version": "1.0",
        "description": f"BornHack order id #{order.id}",
        "callback_url": order.get_coinify_callback_url(request),
        "return_url": order.get_coinify_thanks_url(request),
        "cancel_url": order.get_cancel_url(request),
    }

    # perform the API request
    apireq = coinify_api_request(
        api_method="invoice_create",
        order=order,
        **invoicedict,
    )

    return handle_coinify_api_response(apireq, order, request)
