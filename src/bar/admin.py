from django.contrib import admin

from .models import Product
from .models import ProductCategory


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "category", "in_stock"]
    list_editable = ["in_stock"]
