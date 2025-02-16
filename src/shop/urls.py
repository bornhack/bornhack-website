from django.urls import include
from django.urls import path

from .views import BankTransferView
from .views import CoinifyCallbackView
from .views import CoinifyRedirectView
from .views import CoinifyThanksView
from .views import CreditNoteListView
from .views import DownloadCreditNoteView
from .views import DownloadInvoiceView
from .views import OrderDetailView
from .views import OrderListView
from .views import OrderMarkAsPaidView
from .views import OrderReviewAndPayView
from .views import PayInPersonView
from .views import ProductDetailView
from .views import QuickPayCallbackView
from .views import QuickPayLinkView
from .views import QuickPayThanksView
from .views import ShopIndexView

app_name = "shop"

urlpatterns = [
    path("", ShopIndexView.as_view(), name="index"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),
    path("orders/", OrderListView.as_view(), name="order_list"),
    path(
        "orders/<int:pk>/",
        include(
            [
                path("", OrderDetailView.as_view(), name="order_detail"),
                path(
                    "review/",
                    OrderReviewAndPayView.as_view(),
                    name="order_review_and_pay",
                ),
                path(
                    "invoice/",
                    DownloadInvoiceView.as_view(),
                    name="download_invoice",
                ),
                path(
                    "mark_as_paid/",
                    OrderMarkAsPaidView.as_view(),
                    name="mark_order_as_paid",
                ),
                path(
                    "pay/creditcard/quickpay/",
                    include(
                        [
                            path("", QuickPayLinkView.as_view(), name="quickpay_link"),
                            path(
                                "callback/",
                                QuickPayCallbackView.as_view(),
                                name="quickpay_callback",
                            ),
                            path(
                                "thanks/",
                                QuickPayThanksView.as_view(),
                                name="quickpay_thanks",
                            ),
                        ],
                    ),
                ),
                path(
                    "pay/blockchain/",
                    CoinifyRedirectView.as_view(),
                    name="coinify_pay",
                ),
                path(
                    "pay/blockchain/thanks/",
                    CoinifyThanksView.as_view(),
                    name="coinify_thanks",
                ),
                path(
                    "pay/banktransfer/",
                    BankTransferView.as_view(),
                    name="bank_transfer",
                ),
                path("pay/in_person/", PayInPersonView.as_view(), name="in_person"),
            ],
        ),
    ),
    path(
        "blockchain/callback/",
        CoinifyCallbackView.as_view(),
        name="coinify_intent_callback",
    ),
    path("creditnotes/", CreditNoteListView.as_view(), name="creditnote_list"),
    path(
        "creditnotes/<int:pk>/pdf/",
        DownloadCreditNoteView.as_view(),
        name="download_creditnote",
    ),
]
