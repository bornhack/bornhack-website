from django.conf import settings


def current_order(request):
    if request.user.is_authenticated():
        order = None
        orders = request.user.orders.filter(open__isnull=False)

        if orders:
            order = orders[0]

        return {'current_order': order}
    return {}


def user_has_tickets(request):
    has_tickets = False
    if hasattr(request.user, 'orders') and request.user.orders.filter(
        tickets__product__category__pk=settings.TICKET_CATEGORY_ID
    ).exists():
        has_tickets = True
    return {'has_tickets': has_tickets}

