from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^$', ShopIndexView.as_view(), name='index'),

    url(r'products/(?P<slug>[-_\w+]+)/$', ProductDetailView.as_view(), name='product_detail'),

    url(r'orders/$', OrderListView.as_view(), name='order_list'),
    url(r'orders/(?P<pk>[0-9]+)/$', OrderDetailView.as_view(), name='order_detail'),
    url(r'orders/(?P<pk>[0-9]+)/invoice/$', DownloadInvoiceView.as_view(), name='download_invoice'),

    #url(r'orders/(?P<pk>[0-9]+)/pay/creditcard/$', EpayFormView.as_view(), name='epay_form'),
    #url(r'orders/(?P<pk>[0-9]+)/pay/creditcard/callback/$',EpayCallbackView.as_view(), name='epay_callback'),
    #url(r'orders/(?P<pk>[0-9]+)/pay/creditcard/thanks/$', EpayThanksView.as_view(), name='epay_thanks'),

    url(r'orders/(?P<pk>[0-9]+)/pay/blockchain/$', CoinifyRedirectView.as_view(), name='coinify_pay'),
    url(r'orders/(?P<pk>[0-9]+)/pay/blockchain/callback/$', CoinifyCallbackView.as_view(), name='coinify_callback'),
    url(r'orders/(?P<pk>[0-9]+)/pay/blockchain/thanks/$', CoinifyThanksView.as_view(), name='coinify_thanks'),

    url(r'orders/(?P<pk>[0-9]+)/pay/banktransfer/$', BankTransferView.as_view(), name='bank_transfer'),

    url(r'tickets/$', TicketListView.as_view(), name='ticket_list'),
    url(r'tickets/(?P<pk>\b[0-9A-Fa-f]{8}\b(-\b[0-9A-Fa-f]{4}\b){3}-\b[0-9A-Fa-f]{12}\b)$', TicketDetailView.as_view(), name='ticket_detail'),
]
