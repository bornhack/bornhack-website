from __future__ import annotations

from django.contrib import admin

from .models import CoinifyAPICallback
from .models import CoinifyAPIInvoice
from .models import CoinifyAPIPaymentIntent
from .models import CoinifyAPIRequest
from .models import CreditNote
from .models import CustomOrder
from .models import EpayCallback
from .models import EpayPayment
from .models import Invoice
from .models import Order
from .models import OrderProductRelation
from .models import Product
from .models import ProductCategory
from .models import QuickPayAPICallback
from .models import QuickPayAPIObject
from .models import QuickPayAPIRequest
from .models import Refund
from .models import RefundProductRelation
from .models import SubProductRelation

admin.site.register(EpayCallback)
admin.site.register(CoinifyAPIInvoice)
admin.site.register(CoinifyAPIPaymentIntent)
admin.site.register(CoinifyAPICallback)
admin.site.register(CoinifyAPIRequest)


@admin.register(EpayPayment)
class EpayPaymentAdmin(admin.ModelAdmin):
    list_display = ["uuid", "order", "callback", "txnid"]
    list_filter = ["order"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "customorder", "created", "updated"]


@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "customer",
        "amount",
        "vat",
        "paid",
        "created",
        "updated",
    ]

    list_filter = ["paid"]


@admin.register(CustomOrder)
class CustomOrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "customer",
        "text",
        "amount",
        "vat",
        "paid",
        "created",
        "updated",
    ]

    list_filter = ["paid"]


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.display(
    description="Available from",
)
def available_from(product):
    if product.available_in.lower:
        return product.available_in.lower.strftime("%c")
    return "None"


@admin.display(
    description="Available to",
)
def available_to(product):
    if product.available_in.upper:
        return product.available_in.upper.strftime("%c")
    return "None"


def stock_info(product):
    if product.stock_amount:
        return f"{product.left_in_stock} / {product.stock_amount}"
    return "N/A"


class SubProductInline(admin.TabularInline):
    model = SubProductRelation
    fk_name = "bundle_product"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "ticket_type",
        "price",
        stock_info,
        available_from,
        available_to,
    ]

    list_filter = ["category", "ticket_type"]
    search_fields = ["name"]
    save_as = True

    list_select_related = ["ticket_type", "category", "ticket_type__camp"]

    inlines = [SubProductInline]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.orderproductrelation_set.exists():
            # editing an existing product with existing OPRs, make price readonly
            return ("price",)
        return self.readonly_fields


class ProductInline(admin.TabularInline):
    model = OrderProductRelation


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_form_template = "admin/change_order_form.html"
    readonly_fields = ("paid", "created", "updated")
    search_fields = (
        "products__name",
        "products__description",
        "products__category__name",
    )

    def get_email(self, obj):
        return obj.user.email

    list_display = [
        "id",
        "created",
        "updated",
        "user",
        "get_email",
        "total",
        "payment_method",
        "open",
        "paid",
        "cancelled",
    ]

    list_filter = ["payment_method", "open", "paid", "cancelled", "user"]

    exclude = ["products"]

    inlines = [ProductInline]

    actions = [
        "mark_order_as_paid",
        "mark_order_as_cancelled",
        "create_tickets",
    ]

    def mark_order_as_paid(self, request, queryset):
        for order in queryset.filter(paid=False):
            order.mark_as_paid(request)

    mark_order_as_paid.description = "Mark order(s) as paid"

    def mark_order_as_cancelled(self, request, queryset):
        for order in queryset.filter(cancelled=False):
            order.mark_as_cancelled(request)

    mark_order_as_cancelled.description = "Mark order(s) as cancelled"

    def create_tickets(self, request, queryset):
        for order in queryset.filter(paid=True):
            order.create_tickets(request)

    create_tickets.description = "Create tickets for order(s) (paid only)"


def get_user_email(obj):
    return obj.order.user.email


class RefundInline(admin.TabularInline):
    model = RefundProductRelation
    raw_id_fields = ["opr"]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    inlines = [RefundInline]
    raw_id_fields = ["order"]


@admin.register(QuickPayAPIRequest)
class QuickPayAPIRequestAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "order",
        "method",
        "endpoint",
        "body",
        "headers",
        "query",
        "response_status_code",
        "created",
        "updated",
    ]

    list_filter = ["order", "method", "endpoint"]
    search_fields = ["headers", "body"]


@admin.register(QuickPayAPIObject)
class QuickPayAPIObjectAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "order",
        "object_type",
        "created",
        "updated",
    ]

    list_filter = ["order", "object_type"]
    search_fields = ["object_body"]


@admin.register(QuickPayAPICallback)
class QuickPayAPICallbackAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "qpobject",
        "created",
        "updated",
    ]

    list_filter = ["qpobject"]
    search_fields = ["headers", "body"]
