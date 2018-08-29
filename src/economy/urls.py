from django.urls import path, include
from .views import *

app_name = 'economy'

urlpatterns = [
    path(
        'expenses/',
        ExpenseListView.as_view(),
        name='expense_list'
    ),
    path(
        'expenses/add/',
        ExpenseCreateView.as_view(),
        name='expense_create'
    ),
    path(
        'expenses/<uuid:pk>/',
        ExpenseDetailView.as_view(),
        name='expense_detail'
    ),
    path(
        'expenses/<uuid:pk>/invoice/',
        ExpenseInvoiceView.as_view(),
        name='expense_invoice'
    ),
    path(
        'reimbursements/<uuid:pk>/',
        ReimbursementDetailView.as_view(),
        name='reimbursement_detail'
    ),
]

