from dateutil import relativedelta
from django.conf import settings
from django.utils import timezone

from shop.models import Order
from shop.email import add_order_cancelled_email

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bornhack.%s' % __name__)


def do_work():
    """
    The order cleanup worker scans for orders that are still open
    but are older than ORDER_TTL, and marks those as closed.
    """

    time_threshold = timezone.now() - relativedelta.relativedelta(**{settings.ORDER_TTL_UNIT: settings.ORDER_TTL})

    orders_to_delete = Order.objects.filter(open=True, cancelled=False, created__lt=time_threshold)

    for order in orders_to_delete:
        logger.info(
            "Cancelling order %s since it has been open for more than %s %s" %
            (order.pk, settings.ORDER_TTL, settings.ORDER_TTL_UNIT)
        )
        order.mark_as_cancelled()
        add_order_cancelled_email(order)
