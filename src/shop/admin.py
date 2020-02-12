from django.contrib import admin

from tickets.admin import ShopTicketInline

from .models import (
    CoinifyAPICallback,
    CoinifyAPIInvoice,
    CoinifyAPIRequest,
    CreditNote,
    CustomOrder,
    EpayCallback,
    EpayPayment,
    Invoice,
    Order,
    OrderProductRelation,
    Product,
    ProductCategory,
)

admin.site.register(EpayCallback)
admin.site.register(EpayPayment)
admin.site.register(CoinifyAPIInvoice)
admin.site.register(CoinifyAPICallback)
admin.site.register(CoinifyAPIRequest)


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


def available_from(product):
    if product.available_in.lower:
        return product.available_in.lower.strftime("%c")
    return "None"


available_from.short_description = "Available from"


def available_to(product):
    if product.available_in.upper:
        return product.available_in.upper.strftime("%c")
    return "None"


available_to.short_description = "Available to"


def stock_info(product):
    if product.stock_amount:
        return "{} / {}".format(product.left_in_stock, product.stock_amount)
    return "N/A"


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

    list_editable = ["ticket_type"]

    list_filter = ["category", "ticket_type"]

    search_fields = ["name"]


class ProductInline(admin.TabularInline):
    model = OrderProductRelation


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    change_form_template = "admin/change_order_form.html"
    readonly_fields = ("paid", "created", "updated")

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
        "refunded",
    ]

    list_filter = ["payment_method", "open", "paid", "cancelled", "refunded", "user"]

    exclude = ["products"]

    inlines = [ProductInline, ShopTicketInline]

    actions = [
        "mark_order_as_paid",
        "mark_order_as_refunded",
        "mark_order_as_cancelled",
        "create_tickets",
    ]

    def mark_order_as_paid(self, request, queryset):
        for order in queryset.filter(paid=False):
            order.mark_as_paid(request)

    mark_order_as_paid.description = "Mark order(s) as paid"

    def mark_order_as_refunded(self, request, queryset):
        for order in queryset.filter(refunded=False):
            order.mark_as_refunded(request)

    mark_order_as_refunded.description = "Mark order(s) as refunded"

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
