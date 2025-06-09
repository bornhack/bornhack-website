from __future__ import annotations

from django.urls import include
from django.urls import path

from .views import ChainCreateView
from .views import ChainListView
from .views import CredebtorCreateView
from .views import CredebtorListView
from .views import EconomyDashboardView
from .views import ExpenseCreateView
from .views import ExpenseDeleteView
from .views import ExpenseDetailView
from .views import ExpenseInvoiceView
from .views import ExpenseListView
from .views import ExpenseUpdateView
from .views import ReimbursementCreateView
from .views import ReimbursementDeleteView
from .views import ReimbursementDetailView
from .views import ReimbursementListView
from .views import ReimbursementUpdateView
from .views import RevenueCreateView
from .views import RevenueDeleteView
from .views import RevenueDetailView
from .views import RevenueInvoiceView
from .views import RevenueListView
from .views import RevenueUpdateView

app_name = "economy"

urlpatterns = [
    path("", EconomyDashboardView.as_view(), name="dashboard"),
    # chains
    path(
        "chains/",
        include(
            [
                path("", ChainListView.as_view(), name="chain_list"),
                path("add/", ChainCreateView.as_view(), name="chain_create"),
                path(
                    "<slug:chain_slug>/",
                    include(
                        [
                            path(
                                "",
                                CredebtorListView.as_view(),
                                name="credebtor_list",
                            ),
                            path(
                                "add/",
                                CredebtorCreateView.as_view(),
                                name="credebtor_create",
                            ),
                            path(
                                "<slug:credebtor_slug>/",
                                include(
                                    [
                                        path(
                                            "add_expense/",
                                            ExpenseCreateView.as_view(),
                                            name="expense_create",
                                        ),
                                        path(
                                            "add_revenue/",
                                            RevenueCreateView.as_view(),
                                            name="revenue_create",
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    # expenses
    path(
        "expenses/",
        include(
            [
                path("", ExpenseListView.as_view(), name="expense_list"),
                path(
                    "<uuid:pk>/",
                    include(
                        [
                            path(
                                "",
                                ExpenseDetailView.as_view(),
                                name="expense_detail",
                            ),
                            path(
                                "update/",
                                ExpenseUpdateView.as_view(),
                                name="expense_update",
                            ),
                            path(
                                "delete/",
                                ExpenseDeleteView.as_view(),
                                name="expense_delete",
                            ),
                            path(
                                "invoice/",
                                ExpenseInvoiceView.as_view(),
                                name="expense_invoice",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    # reimbursements
    path(
        "reimbursements/",
        include(
            [
                path("", ReimbursementListView.as_view(), name="reimbursement_list"),
                path(
                    "create/",
                    ReimbursementCreateView.as_view(),
                    name="reimbursement_create",
                ),
                path(
                    "<uuid:pk>/",
                    include(
                        [
                            path(
                                "",
                                ReimbursementDetailView.as_view(),
                                name="reimbursement_detail",
                            ),
                            path(
                                "update/",
                                ReimbursementUpdateView.as_view(),
                                name="reimbursement_update",
                            ),
                            path(
                                "delete/",
                                ReimbursementDeleteView.as_view(),
                                name="reimbursement_delete",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
    # revenue
    path(
        "revenues/",
        include(
            [
                path("", RevenueListView.as_view(), name="revenue_list"),
                path(
                    "<uuid:pk>/",
                    include(
                        [
                            path(
                                "",
                                RevenueDetailView.as_view(),
                                name="revenue_detail",
                            ),
                            path(
                                "update/",
                                RevenueUpdateView.as_view(),
                                name="revenue_update",
                            ),
                            path(
                                "delete/",
                                RevenueDeleteView.as_view(),
                                name="revenue_delete",
                            ),
                            path(
                                "invoice/",
                                RevenueInvoiceView.as_view(),
                                name="revenue_invoice",
                            ),
                        ],
                    ),
                ),
            ],
        ),
    ),
]
