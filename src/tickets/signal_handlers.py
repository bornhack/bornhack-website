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
    from tickets.models import ShopTicket
    stats = ", ".join(["%s: %s" % (tickettype['product__name'].replace("BornHack 2017 ", ""), tickettype['total']) for tickettype in ShopTicket.objects.filter(product__name__startswith="BornHack 2017").exclude(product__name__startswith="BornHack 2017 One Day").values('product__name').annotate(total=Count('product__name')).order_by('-total')])

    onedaystats = Ticket.objects.filter(product__name__startswith="BornHack 2017 One Day Ticket").count()
    onedaychildstats = Ticket.objects.filter(product__name__startswith="BornHack 2017 One Day Children").count()

    # queue the messages
    from ircbot.models import OutgoingIrcMessage
    OutgoingIrcMessage.objects.create(
        target=target,
        message="%s sold!" % instance.product.name,
        timeout=timezone.now()+timedelta(minutes=10)
    )
    OutgoingIrcMessage.objects.create(
        target=target,
        message="Totals: %s, 1day: %s, 1day child: %s" % (stats, onedaystats, onedaychildstats)[:200],
        timeout=timezone.now()+timedelta(minutes=10)
    )

