from django.contrib import admin

from . import models

admin.site.register(models.EpayCallback)
admin.site.register(models.EpayPayment)
admin.site.register(models.CoinifyAPIInvoice)
admin.site.register(models.CoinifyAPICallback)
admin.site.register(models.Invoice)

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
    list_display = [
        'user',
        'camp',
        'payment_method',
        'paid',
    ]

    list_filter = [
        'user',
        'camp',
        'payment_method',
        'paid',
    ]

    exclude = ['products']

    inlines = [ProductInline, TicketInline]

    actions = ['mark_order_as_paid']

    def mark_order_as_paid(self, request, queryset):
        for order in queryset.filter(paid=False):
            order.mark_as_paid()
    mark_order_as_paid.description = 'Mark order(s) as paid'


@admin.register(models.Ticket)
class TicketAdmin(admin.ModelAdmin):
    pass