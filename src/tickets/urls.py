from django.conf.urls import url

from .views import (
    ShopTicketListView,
    ShopTicketDownloadView,
    ShopTicketDetailView
)

urlpatterns = [
    url(
        r'^$',
        ShopTicketListView.as_view(),
        name='shopticket_list'
    ),
    url(
        r'^(?P<pk>\b[0-9A-Fa-f]{8}\b(-\b[0-9A-Fa-f]{4}\b){3}-\b[0-9A-Fa-f]{12}\b)/download/$',
        ShopTicketDownloadView.as_view(),
        name='shopticket_download'
    ),
    url(
        r'^(?P<pk>\b[0-9A-Fa-f]{8}\b(-\b[0-9A-Fa-f]{4}\b){3}-\b[0-9A-Fa-f]{12}\b)/edit/$',
        ShopTicketDetailView.as_view(),
        name='shopticket_edit'
    ),
]
