from django.urls import path, include
from .views import *

app_name = 'economy'

urlpatterns = [
    path(
        '',
        EconomyDashboardView.as_view(),
        name='dashboard'
    ),

    # expenses
    path(
        'expenses/',
        include([
            path(
                '',
                ExpenseListView.as_view(),
                name='expense_list'
            ),
            path(
                'add/',
                ExpenseCreateView.as_view(),
                name='expense_create'
            ),
            path(
                '<uuid:pk>/',
                include([
                    path(
                        '',
                        ExpenseDetailView.as_view(),
                        name='expense_detail'
                    ),
                    path(
                        'update/',
                        ExpenseUpdateView.as_view(),
                        name='expense_update'
                    ),
                    path(
                        'delete/',
                        ExpenseDeleteView.as_view(),
                        name='expense_delete'
                    ),
                    path(
                        'invoice/',
                        ExpenseInvoiceView.as_view(),
                        name='expense_invoice'
                    ),
                ]),
            ),
        ]),
    ),

    # reimbursements
    path(
        'reimbursements/',
        include([
            path(
                '',
                ReimbursementListView.as_view(),
                name='reimbursement_list'
            ),
            path(
                '<uuid:pk>/',
                ReimbursementDetailView.as_view(),
                name='reimbursement_detail'
            ),
        ]),
    ),

    # revenue
    path(
        'revenues/',
        include([
            path(
                '',
                RevenueListView.as_view(),
                name='revenue_list'
            ),
            path(
                'add/',
                RevenueCreateView.as_view(),
                name='revenue_create'
            ),
            path(
                '<uuid:pk>/',
                include([
                    path(
                        '',
                        RevenueDetailView.as_view(),
                        name='revenue_detail'
                    ),
                    path(
                        'update/',
                        RevenueUpdateView.as_view(),
                        name='revenue_update'
                    ),
                    path(
                        'delete/',
                        RevenueDeleteView.as_view(),
                        name='revenue_delete'
                    ),
                    path(
                        'invoice/',
                        RevenueInvoiceView.as_view(),
                        name='revenue_invoice'
                    ),
                ]),
            ),
        ]),
    ),
]

