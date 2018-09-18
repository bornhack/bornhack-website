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
                ExpenseDetailView.as_view(),
                name='expense_detail'
            ),
            path(
                '<uuid:pk>/invoice/',
                ExpenseInvoiceView.as_view(),
                name='expense_invoice'
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
                RevenueDetailView.as_view(),
                name='revenue_detail'
            ),
            path(
                '<uuid:pk>/invoice/',
                RevenueInvoiceView.as_view(),
                name='revenue_invoice'
            ),
        ]),
    ),
]

