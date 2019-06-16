from django.urls import path

from .views import ShopTicketListView, ShopTicketDownloadView, ShopTicketDetailView

app_name = "tickets"

urlpatterns = [
    path("", ShopTicketListView.as_view(), name="shopticket_list"),
    path(
        "<uuid:pk>/download/",
        ShopTicketDownloadView.as_view(),
        name="shopticket_download",
    ),
    path("<uuid:pk>/edit/", ShopTicketDetailView.as_view(), name="shopticket_edit"),
]
