from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'orders/(?P<pk>[0-9]+)/pay/creditcard/$', EpayFormView.as_view(), name='epay_form'),
    url(r'epay_callback/', EpayCallbackView.as_view(), name='epay_callback'),
    url(r'^$', ShopIndexView.as_view(), name='index'),
    url(r'products/(?P<slug>[-_\w+]+)/$', ProductDetailView.as_view(), name='product_detail'),
    url(r'orders/$', OrderListView.as_view(), name='order_list'),
    url(r'orders/(?P<pk>[0-9]+)/$', OrderDetailView.as_view(), name='order_detail'),
    # url(r'orders/(?P<pk>[0-9]+)/checkout/$', CheckoutView.as_view(), name='checkout'),
]
