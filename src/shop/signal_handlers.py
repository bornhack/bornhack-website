from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.db.models import Count
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def ticket_created(sender, instance, created, **kwargs):
    # only send a message when a ticket is created
    if not created:
        return

    # queue an IRC message to the orga channel if any is defined, otherwise for the default channel
    target = settings.IRCBOT_CHANNELS['orga'] if 'orga' in settings.IRCBOT_CHANNELS else settings.IRCBOT_CHANNELS['default']

    # get ticket stats, FIXME: Camp name is hardcoded here for now
    from shop.models import Ticket
    stats = ", ".join(["%s: %s" % (tickettype['product__name'], tickettype['total']) for tickettype in Ticket.objects.filter(product__name__startswith="BornHack 2017").values('product__name').annotate(total=Count('product__name')).order_by('product__name')])

    # queue the message
    from ircbot.models import OutgoingIrcMessage
    OutgoingIrcMessage.objects.create(
        target=target,
        message="%s sold! Totals: %s" % (instance.product.name, stats),
        timeout=timezone.now()+timedelta(minutes=10)
    )

