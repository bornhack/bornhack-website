import json
import logging

import requests
from django.conf import settings

from .models import CoinifyAPICallback
from .models import CoinifyAPIPaymentIntent
from .models import CoinifyAPIRequest

logger = logging.getLogger("bornhack.%s" % __name__)


def process_coinify_payment_intent_json(intentjson, order, request):
    # create or update the intent object in our database
    coinifyintent, created = CoinifyAPIPaymentIntent.objects.update_or_create(
        coinify_id=intentjson["id"],
        order=order,
        defaults={"paymentintentjson": intentjson},
    )

    # if the order is paid in full call the mark as paid method now
    if "state" in intentjson:
        if intentjson["state"] == "completed" and not coinifyintent.order.paid:
            coinifyintent.order.mark_as_paid(request=request)

    return coinifyintent


def save_coinify_callback(request, order):
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
    callbackobject = CoinifyAPICallback.objects.create(
        headers=headerdict,
        body=request.body,
        payload=parsed,
        order=order,
    )

    return callbackobject


def coinify_api_request(api_method, order, payload):
    url = f"{settings.COINIFY_API_URL}{api_method}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-KEY": settings.COINIFY_API_KEY,
    }
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
    except requests.exceptions.RequestException as E:
        logger.error("requests exception during coinify api request: %s" % E)
        return False

    # save this API request to the database
    req = CoinifyAPIRequest.objects.create(
        order=order,
        method=api_method,
        payload=payload,
        response=response.json(),
    )
    logger.debug("saved coinify api request %s in db" % req.id)

    return req


def handle_coinify_api_response(apireq, order, request):
    if apireq.method == "payment-intents":
        # Parse api response
        if "paymentWindowUrl" in apireq.response:
            # save this new coinify intent to the DB
            coinifyintent = process_coinify_payment_intent_json(
                intentjson=apireq.response,
                order=order,
                request=request,
            )
            return coinifyintent
        else:
            api_error = apireq.json()
            logger.error(
                "coinify API error: {} ({})".format(
                    api_error["errorMessage"],
                    api_error["errorCode"],
                ),
            )
            return False
    else:
        logger.error("coinify api method not supported" % apireq.method)
        return False


#################################################################
# API CALLS


def create_coinify_payment_intent(order, request):
    # put args for API request together
    intentdict = {
        "amount": float(order.total),
        "currency": "DKK",
        "pluginIdentifier": "BornHack webshop",
        "orderId": str(order.id),
        "customerId": "bbca76fa-1337-439a-ae29-a3c2c2c84c4b",
        "customerEmail": "coinifycustomer@example.com",
        "memo": "BornHack order id #%s" % order.id,
        "successUrl": order.get_coinify_thanks_url(request),
        "failureUrl": order.get_cancel_url(request),
    }

    # perform the API request
    apireq = coinify_api_request(
        api_method="payment-intents",
        order=order,
        payload=intentdict,
    )

    coinifyintent = handle_coinify_api_response(apireq, order, request)
    return coinifyintent
