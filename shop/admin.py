from django.contrib import admin

from . import models

admin.site.register(models.EpayCallback)
admin.site.register(models.EpayPayment)


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

    inlines = [ProductInline]


@admin.register(models.Ticket)
class TicketAdmin(admin.ModelAdmin):
    pass