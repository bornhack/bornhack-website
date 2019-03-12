from django.contrib import admin
from .models import Expense, Reimbursement, Revenue


### expenses

def approve_expenses(modeladmin, request, queryset):
    for expense in queryset.all():
        expense.approve(request)
approve_expenses.short_description = "Approve Expenses"


def reject_expenses(modeladmin, request, queryset):
    for expense in queryset.all():
        expense.reject(request)
reject_expenses.short_description = "Reject Expenses"


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_filter = ['camp', 'responsible_team', 'approved', 'user']
    list_display = ['user', 'description', 'invoice_date', 'amount', 'camp', 'responsible_team', 'approved', 'reimbursement']
    search_fields = ['description', 'amount', 'uuid']
    actions = [approve_expenses, reject_expenses]


### revenues

def approve_revenues(modeladmin, request, queryset):
    for revenue in queryset.all():
        revenue.approve(request)
approve_revenues.short_description = "Approve Revenues"


def reject_revenues(modeladmin, request, queryset):
    for revenue in queryset.all():
        revenue.reject(request)
reject_revenues.short_description = "Reject Revenues"


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_filter = ['camp', 'responsible_team', 'approved', 'user']
    list_display = ['user', 'description', 'invoice_date', 'amount', 'camp', 'responsible_team', 'approved']
    search_fields = ['description', 'amount', 'user']
    actions = [approve_revenues, reject_revenues]


### reimbursements

@admin.register(Reimbursement)
class ReimbursementAdmin(admin.ModelAdmin):
    def get_amount(self, obj):
        return obj.amount
    list_filter = ['camp', 'user', 'reimbursement_user', 'paid']
    list_display = ['camp', 'user', 'reimbursement_user', 'paid', 'notes', 'get_amount']
    search_fields = ['user__username', 'reimbursement_user__username', 'notes']

