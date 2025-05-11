import json
import logging

from django.conf import settings
from quickpay_api_client import QPClient
from quickpay_api_client.exceptions import ApiError

from .models import QuickPayAPIRequest

# from .models import QuickPayPayment

logger = logging.getLogger("bornhack.%s" % __name__)


class QuickPay:
    """A small wrapper around the QuickPay client to log API requests and responses."""

    def __init__(self):
        """Initialise the QuickPay client."""
        self.client = QPClient(f":{settings.QUICKPAY_API_KEY}")

    def do_request(self, request):
        """Perform an API request and save the response."""
        # make sure we include request id
        if "x-bornhack-quickpay-request-id" not in request.headers:
            request.headers["x-bornhack-quickpay-request-id"] = str(request.uuid)
            request.save()
        # call the method
        method = getattr(self.client, request.method.lower())
        try:
            status, body, headers = method(
                path=request.endpoint,
                body=request.body,
                headers=request.headers if request.headers else None,
                query=request.query if request.query else None,
                raw=True,
            )
        except ApiError as e:
            logger.error(f"QuickPay API error: {e}")
            request.response_status_code = e.status_code
            # no headers returned in the ApiError object
            # request.response_headers = dict(e.headers)
            request.response_body = e.body
            request.save()
            return None
        # save the response in the request object
        request.response_status_code = status
        request.response_headers = dict(headers)
        request.response_body = json.loads(body)
        request.save()
        # create or update related QuickPayAPIObject
        if request.response_status_code in [200, 201]:
            return request.create_or_update_object()

    def create_payment(self, order):
        """Create and return a QuickPayAPIPayment object."""
        qpr = QuickPayAPIRequest.objects.create(
            order=order,
            method="POST",
            endpoint="/payments",
            body={
                "order_id": str(order.id).zfill(4),
                "currency": "DKK",
            },
        )
        qpr.save()
        payment = self.do_request(qpr)
        return payment

    def get_payment_link(self, payment, request):
        """Get a payment link for this payment."""
        body = {
            "amount": int(payment.order.total * 100),
            "continue_url": payment.order.get_quickpay_accept_url(request),
            "cancel_url": payment.order.get_cancel_url(request),
            "callback_url": payment.order.get_quickpay_callback_url(request),
            "auto_capture": True,
        }
        qpr = QuickPayAPIRequest.objects.create(
            order=payment.order,
            method="PUT",
            endpoint=f"/payments/{payment.object_body['id']}/link",
            body=body,
        )
        self.do_request(qpr)
        return qpr.response_body["url"]
