from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import (
    InfoItem,
    InfoCategory
)


@admin.register(InfoItem)
class InfoItemAdmin(VersionAdmin):
    list_filter = ['category', 'category__camp',]
    list_display = ['headline',]


class InfoItemInlineAdmin(admin.StackedInline):
    model = InfoItem
    list_filter = ['category', 'category__camp',]
    list_display = ['headline',]


@admin.register(InfoCategory)
class InfoCategorydmin(admin.ModelAdmin):
    list_filter = ['camp',]
    list_display = ['headline',]
    search_fields = ['headline', 'body']
    inlines = [InfoItemInlineAdmin]
