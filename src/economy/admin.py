from __future__ import annotations

from django.contrib import admin

from .models import Bank
from .models import BankAccount
from .models import BankTransaction
from .models import Chain
from .models import CoinifyBalance
from .models import CoinifyInvoice
from .models import CoinifyPaymentIntent
from .models import CoinifyPayout
from .models import CoinifySettlement
from .models import Credebtor
from .models import EpayTransaction
from .models import Expense
from .models import Pos
from .models import PosProduct
from .models import PosReport
from .models import PosSale
from .models import PosTransaction
from .models import Reimbursement
from .models import Revenue
from .models import ZettleBalance
from .models import ZettleReceipt

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


@admin.action(
    description="Approve Expenses",
)
def approve_expenses(modeladmin, request, queryset):
    for expense in queryset.all():
        expense.approve(request)


@admin.action(
    description="Reject Expenses",
)
def reject_expenses(modeladmin, request, queryset):
    for expense in queryset.all():
        expense.reject(request)


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


@admin.action(
    description="Approve Revenues",
)
def approve_revenues(modeladmin, request, queryset):
    for revenue in queryset.all():
        revenue.approve(request)


@admin.action(
    description="Reject Revenues",
)
def reject_revenues(modeladmin, request, queryset):
    for revenue in queryset.all():
        revenue.reject(request)


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
    list_display = ["name", "team", "external_id"]
    list_filter = ["team"]


@admin.register(PosReport)
class PosReportAdmin(admin.ModelAdmin):
    list_display = ["uuid", "pos"]


@admin.register(PosProduct)
class PosProductAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "external_id",
        "brand_name",
        "name",
        "description",
        "sales_price",
        "unit_size",
        "size_unit",
        "abv",
        "tags",
    ]


@admin.register(PosTransaction)
class PosTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "pos",
        "external_transaction_id",
        "external_user_id",
        "timestamp",
    ]
    list_filter = ["pos", "external_user_id"]
    date_hierarchy = "timestamp"


@admin.register(PosSale)
class PosSaleAdmin(admin.ModelAdmin):
    list_display = ["uuid", "transaction", "product", "sales_price"]


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


@admin.register(CoinifyPaymentIntent)
class CoinifyPaymentIntentAdmin(admin.ModelAdmin):
    list_display = [
        "coinify_id",
        "coinify_created",
        "requested_amount",
        "requested_currency",
        "amount",
        "currency",
        "state",
        "state_reason",
        "reference_type",
        "original_order_id",
        "order",
        "api_payment_intent",
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


@admin.register(CoinifySettlement)
class CoinifySettlementAdmin(admin.ModelAdmin):
    list_display = [
        "settlement_id",
        "create_time",
        "account",
        "gross_amount",
        "fee",
        "net_amount",
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


################################
# zettle


@admin.register(ZettleBalance)
class ZettleBalanceAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "statement_time",
        "payment_time",
        "payment_reference",
        "description",
        "amount",
        "balance",
    ]
    search_fields = ["description"]


@admin.register(ZettleReceipt)
class ZettleReceiptAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "zettle_created",
        "receipt_number",
        "total",
        "vat",
        "fee",
        "net",
        "payment_method",
        "card_issuer",
        "staff",
        "description",
    ]
    list_filter = ["payment_method", "card_issuer"]
    search_fields = ["description", "receipt_number"]
