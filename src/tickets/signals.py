from django.conf import settings
from datetime import (
    timedelta,
    datetime
)

def ticket_changed(sender, instance, created, **kwargs):
    """
    This signal is called every time a ShopTicket is saved
    """
    # only queue an IRC message when a new ticket is created
    if not created:
        return

    # queue an IRC message to the orga channel if defined,
    # otherwise for the default channel
    target = settings.IRCBOT_CHANNELS['orga'] if 'orga' in settings.IRCBOT_CHANNELS else settings.IRCBOT_CHANNELS['default']

    # get ticket stats
    from .models import ShopTicket
    ticket_prefix = "BornHack {}".format(datetime.now().year)

    stats = ", ".join(
        [
            "{}: {}".format(
                tickettype['product__name'].replace(
                    "{} ".format(ticket_prefix),
                    ""
                ),
                tickettype['total']
            ) for tickettype in ShopTicket.objects.filter(
                product__name__startswith=ticket_prefix
            ).exclude(
                product__name__startswith="{} One Day".format(ticket_prefix)
            ).values(
                'product__name'
            ).annotate(
                total=Count('product__name')
            ).order_by('-total')
        ]
    )

    onedaystats = ShopTicket.objects.filter(
        product__name__startswith="{} One Day Ticket".format(ticket_prefix)
    ).count()
    onedaychildstats = ShopTicket.objects.filter(
        product__name__startswith="{} One Day Children".format(ticket_prefix)
    ).count()

    # queue the messages
    from ircbot.models import OutgoingIrcMessage
    OutgoingIrcMessage.objects.create(
        target=target,
        message="%s sold!" % instance.product.name,
        timeout=timezone.now()+timedelta(minutes=10)
    )
    OutgoingIrcMessage.objects.create(
        target=target,
        message="Totals: {}, 1day: {}, 1day child: {}".format(
            stats,
            onedaystats,
            onedaychildstats
        )[:200],
        timeout=timezone.now()+timedelta(minutes=10)
    )

