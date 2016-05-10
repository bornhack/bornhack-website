from django.conf.urls import url

from .views import (
    ShopIndexView,
    # EpayView,
    # EpayCallbackView,
)

urlpatterns = [
    #url(r'order/$', TicketOrderView.as_view(), name='order'),
    #url(
        #r'pay/credit_card/(?P<ticket_id>[a-zA-Z0-9\-]+)/$',
        #EpayView.as_view(),
        #name='epay_form'
    #),
    #url(
        #r'epay_callback/',
        #EpayCallbackView,
        #name='epay_callback'
    #),
    #url(
        #r'detail/(?P<pk>[a-zA-Z0-9\-]+)/$',
        #TicketDetailView.as_view(),
        #name='detail'
    #),
    url(r'$', ShopIndexView.as_view(), name='index'),
]
