from django.contrib import admin

from .models import Order, ProductCategory, Product, OrderProductRelation


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category',
        'price',
        'available_in',
    ]


class ProductInline(admin.TabularInline):
    model = OrderProductRelation


@admin.register(Order)
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

