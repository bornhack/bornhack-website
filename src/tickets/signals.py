from datetime import datetime

from django.db.models import Count

from events.handler import handle_team_event


def ticket_changed(sender, instance, created, **kwargs):
    """
    This signal is called every time a ShopTicket is saved
    """
    # only trigger an event when a new ticket is created
    if not created:
        return

    # get ticket stats
    from .models import ShopTicket

    # TODO: this is nasty, get the prefix some other way
    ticket_prefix = "BornHack {}".format(datetime.now().year)

    stats = ", ".join(
        [
            "{}: {}".format(
                tickettype["product__name"].replace("{} ".format(ticket_prefix), ""),
                tickettype["total"],
            )
            for tickettype in ShopTicket.objects.filter(
                product__name__startswith=ticket_prefix
            )
            .exclude(product__name__startswith="{} One Day".format(ticket_prefix))
            .values("product__name")
            .annotate(total=Count("product__name"))
            .order_by("-total")
        ]
    )

    onedaystats = ShopTicket.objects.filter(
        product__name__startswith="{} One Day Ticket".format(ticket_prefix)
    ).count()
    onedaychildstats = ShopTicket.objects.filter(
        product__name__startswith="{} One Day Children".format(ticket_prefix)
    ).count()

    # queue the messages
    handle_team_event(
        eventtype="ticket_created", irc_message="%s sold!" % instance.product.name
    )
    # limit this one to a length of 200 because IRC is nice
    handle_team_event(
        eventtype="ticket_created",
        irc_message="Totals: {}, 1day: {}, 1day child: {}".format(
            stats, onedaystats, onedaychildstats
        )[:200],
    )
