from django.conf.urls import url

from .views import BuyTicketView, TicketIndexView, TicketDetailView

urlpatterns = [
    url(r'buy/$', BuyTicketView.as_view(), name='buy'),
    url(
        r'detail/(?P<pk>[a-zA-Z0-9\-]+)/$',
        TicketDetailView.as_view(),
        name='detail'
    ),
    url(r'$', TicketIndexView.as_view(), name='index'),
]
