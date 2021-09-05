from django.contrib import admin

from .models import (
    Bank,
    BankAccount,
    BankTransaction,
    Chain,
    CoinifyBalance,
    CoinifyInvoice,
    CoinifyPayout,
    Credebtor,
    EpayTransaction,
    Expense,
    Pos,
    PosReport,
    Reimbursement,
    Revenue,
)

###############################
# chains and credebtors


@admin.register(Chain)
class ChainAdmin(admin.ModelAdmin):
    list_filter = ["name"]
    list_display = ["name", "notes"]
    search_fields = ["name", "notes"]


@admin.register(Credebtor)
class CredebtorAdmin(admin.ModelAdmin):
    list_filter = ["chain", "name"]
    list_display = ["name", "chain", "address", "notes"]
    search_fields = ["chain", "name", "address", "notes"]


###############################
# expenses


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
    list_filter = [
        "camp",
        "creditor__chain",
        "creditor",
        "responsible_team",
        "approved",
        "user",
    ]
    list_display = [
        "user",
        "description",
        "invoice_date",
        "amount",
        "camp",
        "creditor",
        "responsible_team",
        "approved",
        "reimbursement",
    ]
    search_fields = ["description", "amount", "uuid"]
    actions = [approve_expenses, reject_expenses]


###############################
# revenues


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
    list_filter = ["camp", "responsible_team", "approved", "user"]
    list_display = [
        "user",
        "description",
        "invoice_date",
        "amount",
        "camp",
        "responsible_team",
        "approved",
    ]
    search_fields = ["description", "amount", "user"]
    actions = [approve_revenues, reject_revenues]


###############################
# reimbursements


@admin.register(Reimbursement)
class ReimbursementAdmin(admin.ModelAdmin):
    def get_amount(self, obj):
        return obj.amount

    list_filter = ["camp", "user", "reimbursement_user", "paid"]
    list_display = ["camp", "user", "reimbursement_user", "paid", "notes", "get_amount"]
    search_fields = ["user__username", "reimbursement_user__username", "notes"]


################################
# pos


@admin.register(Pos)
class PosAdmin(admin.ModelAdmin):
    list_display = ["name", "team"]
    list_filter = ["team"]


@admin.register(PosReport)
class PosReportAdmin(admin.ModelAdmin):
    list_display = ["uuid", "pos"]


################################
# bank


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ["pk", "name"]


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ["pk", "bank_account", "date", "text", "amount", "balance"]
    list_filter = ["bank_account"]


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "bank",
        "name",
        "reg_no",
        "account_no",
        "start_date",
        "end_date",
    ]
    list_filter = ["bank"]


################################
# coinify


@admin.register(CoinifyInvoice)
class CoinifyInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "coinify_id",
        "coinify_id_alpha",
        "coinify_created",
        "payment_amount",
        "payment_currency",
        "payment_btc_amount",
        "description",
        "custom",
        "credited_amount",
        "credited_currency",
        "state",
        "payment_type",
        "original_payment_id",
    ]


@admin.register(CoinifyPayout)
class CoinifyPayoutAdmin(admin.ModelAdmin):
    list_display = [
        "coinify_id",
        "coinify_created",
        "amount",
        "fee",
        "transferred",
        "currency",
        "btc_txid",
    ]


@admin.register(CoinifyBalance)
class CoinifyBalanceAdmin(admin.ModelAdmin):
    list_display = ["date", "btc", "dkk", "eur"]


################################
# epay


@admin.register(EpayTransaction)
class EpayTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_id",
        "order_id",
        "currency",
        "auth_date",
        "auth_amount",
        "captured_date",
        "captured_amount",
        "card_type",
        "description",
        "transaction_fee",
    ]
    list_filter = ["card_type"]
    search_fields = ["description"]
