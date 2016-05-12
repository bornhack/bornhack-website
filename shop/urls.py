from django.conf.urls import url
import views

urlpatterns = [
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
    url(r'$', ShopIndexView.as_view(), name='index'),
    url(r'orders/(?P<pk>[0-9]+)/$', OrderDetailView.as_view(), name='order_detail'),
    url(r'orders/(?P<pk>[0-9]+)/checkout/$', CheckoutView.as_view(), name='checkout'),
]
