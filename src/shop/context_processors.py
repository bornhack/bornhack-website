from __future__ import annotations


def current_order(request):
    if request.user.is_authenticated:
        order = None
        orders = request.user.orders.filter(open__isnull=False)

        if orders:
            order = orders[0]

        return {"current_order": order}
    return {}
