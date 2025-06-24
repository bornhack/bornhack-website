from __future__ import annotations

from django.urls import path

from .views import ShopTicketDetailView
from .views import TicketDownloadView
from .views import shop_ticket_list_view

app_name = "tickets"

urlpatterns = [
    path("", shop_ticket_list_view, name="shopticket_list"),
    path(
        "<uuid:pk>/download/",
        TicketDownloadView.as_view(),
        name="ticket_download",
    ),
    path("<uuid:pk>/edit/", ShopTicketDetailView.as_view(), name="shopticket_edit"),
]
