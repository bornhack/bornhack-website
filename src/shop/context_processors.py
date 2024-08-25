from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest


def current_order(request: HttpRequest):
    if request.user.is_authenticated:
        order = None
        orders = request.user.orders.filter(open__isnull=False)

        if orders:
            order = orders[0]

        return {"current_order": order}
    return {}
