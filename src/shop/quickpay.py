import json
import logging

from django.conf import settings
from quickpay_api_client import QPClient
from quickpay_api_client.exceptions import ApiError

from .models import QuickPayAPIRequest, QuickPayPayment

logger = logging.getLogger("bornhack.%s" % __name__)


class QuickPay:
    """A small wrapper around the QuickPay client to log API requests and responses."""

    def __init__(self):
        """Initialise the QuickPay client."""
        self.client = QPClient(f":{settings.QUICKPAY_API_KEY}")

    def do_request(self, request):
        """Perform an API request and save the response."""
        method = getattr(self.client, request.method.lower())
        try:
            status, body, headers = method(
                path=request.endpoint,
                body=json.dumps(request.body),
                headers=request.headers,
                query=request.query,
                raw=True,
            )
        except ApiError as e:
            logger.error(f"QuickPay API error: {e}")
            request.response_status_code = e.status_code
            request.response_body = e.body
            request.save()
            return
        request.response_status_code = status
        request.response_headers = headers
        request.response_body = body
        request.save()

    def create_payment(self, order):
        """Create and return a QuickPayAPIPayment object."""
        qpr = QuickPayAPIRequest.objects.create(
            order=order,
            method="POST",
            endpoint="/payments",
            body={
                "order_id": str(order.id).zfill(5),
                "currency": "DKK",
            },
        )
        qpr.headers = {"x-bornhack-quickpay-request-id": str(qpr.uuid)}
        self.do_request(qpr)
        if qpr.response_status_code == 200:
            return QuickPayPayment.objects.create(
                qpid=qpr.response_body["id"],
                body=qpr.response_body,
            )

    def get_payment_link(self, payment):
        """Get a payment link for this payment."""
        qpr = QuickPayAPIRequest.objects.create(
            order=payment.request.order,
            method="PUT",
            endpoint="/payments/{payment['id']}/link",
            body={
                "amount": payment.request.order.total,
                "continue_url": payment.request.order.get_quickpay_accept_url(),
                "cancel_url": payment.request.order.get_cancel_url(),
                "callback_url": payment.request.order.get_quickpay_callback_url(),
                "auto_capture": True,
            },
            raw=True,
        )
        self.do_request(qpr)
        return qpr.body["url"]
