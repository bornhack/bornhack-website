from django.contrib import admin

from . import models

admin.site.register(models.EpayCallback)
admin.site.register(models.EpayPayment)
admin.site.register(models.CoinifyAPIInvoice)
admin.site.register(models.CoinifyAPICallback)
admin.site.register(models.Invoice)
admin.site.register(models.CreditNote)
admin.site.register(models.Ticket)


@admin.register(models.ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
    ]


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category',
        'price',
        'available_in',
    ]


class ProductInline(admin.TabularInline):
    model = models.OrderProductRelation


class TicketInline(admin.TabularInline):
    model = models.Ticket
    exclude = ['qrcode_base64']



@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    change_form_template = 'admin/change_order_form.html'

    def get_email(self, obj):
        return obj.user.email

    list_display = [
        'id',
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
        'camp',
        'payment_method',
        'open',
        'paid',
        'cancelled',
        'refunded',
        'user',
    ]

    exclude = ['products']

    inlines = [ProductInline, TicketInline]

    actions = ['mark_order_as_paid', 'mark_order_as_refunded']

    def mark_order_as_paid(self, request, queryset):
        for order in queryset.filter(paid=False):
            order.mark_as_paid()
    mark_order_as_paid.description = 'Mark order(s) as paid'

    def mark_order_as_refunded(self, request, queryset):
        for order in queryset.filter(refunded=False):
            order.mark_as_refunded()
    mark_order_as_refunded.description = 'Mark order(s) as refunded'

