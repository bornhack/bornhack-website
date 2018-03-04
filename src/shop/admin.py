from django.contrib import admin

from . import models

admin.site.register(models.EpayCallback)
admin.site.register(models.EpayPayment)
admin.site.register(models.CoinifyAPIInvoice)
admin.site.register(models.CoinifyAPICallback)
admin.site.register(models.CoinifyAPIRequest)
admin.site.register(models.Invoice)
admin.site.register(models.CreditNote)


@admin.register(models.CustomOrder)
class CustomOrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'customer',
        'text',
        'amount',
        'vat',
        'paid',
    ]

    list_filter = [
        'paid',
    ]


@admin.register(models.ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
    ]


def available_from(product):
    if product.available_in.lower:
        return product.available_in.lower.strftime("%c")
    return "None"
available_from.short_description = 'Available from'


def available_to(product):
    if product.available_in.upper:
        return product.available_in.upper.strftime("%c")
    return "None"
available_to.short_description = 'Available to'


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category',
        'ticket_type',
        'price',
        'description',
        available_from,
        available_to
    ]

    search_fields = ['name']


class ProductInline(admin.TabularInline):
    model = models.OrderProductRelation


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    change_form_template = 'admin/change_order_form.html'
    readonly_fields = (
        'paid',
        'created',
        'updated',
    )

    def get_email(self, obj):
        return obj.user.email

    list_display = [
        'id',
        'created',
        'updated',
        'user',
        'get_email',
        'total',
        'payment_method',
        'open',
        'paid',
        'cancelled',
        'refunded',
    ]

    list_filter = [
        'payment_method',
        'open',
        'paid',
        'cancelled',
        'refunded',
        'user',
    ]

    exclude = ['products']

    inlines = [ProductInline]

    actions = ['mark_order_as_paid', 'mark_order_as_refunded']

    def mark_order_as_paid(self, request, queryset):
        for order in queryset.filter(paid=False):
            order.mark_as_paid(request)
    mark_order_as_paid.description = 'Mark order(s) as paid'

    def mark_order_as_refunded(self, request, queryset):
        for order in queryset.filter(refunded=False):
            order.mark_as_refunded(request)
    mark_order_as_refunded.description = 'Mark order(s) as refunded'


def get_user_email(obj):
    return obj.order.user.email

