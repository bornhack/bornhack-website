from django.contrib import admin
from .models import Expense, Reimbursement


def approve_expenses(modeladmin, request, queryset):
    for expense in queryset.all():
        expense.approve()
approve_expenses.short_description = "Approve Expenses"


def reject_expenses(modeladmin, request, queryset):
    for expense in queryset.all():
        expense.reject()
reject_expenses.short_description = "Reject Expenses"


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_filter = ['camp', 'responsible_team', 'approved', 'user', 'reimbursement']
    list_display = ['user', 'description', 'amount', 'camp', 'responsible_team', 'approved', 'reimbursement']
    search_fields = ['description', 'amount', 'user']
    actions = [approve_expenses, reject_expenses]

