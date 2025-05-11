from __future__ import annotations

from django.urls import path

from .views import ShopTicketDetailView
from .views import ShopTicketDownloadView
from .views import shop_ticket_list_view

app_name = "tickets"

urlpatterns = [
    path("", shop_ticket_list_view, name="shopticket_list"),
    path(
        "<uuid:pk>/download/",
        ShopTicketDownloadView.as_view(),
        name="shopticket_download",
    ),
    path("<uuid:pk>/edit/", ShopTicketDetailView.as_view(), name="shopticket_edit"),
]
