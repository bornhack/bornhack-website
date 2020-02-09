from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import InfoCategory, InfoItem


@admin.register(InfoItem)
class InfoItemAdmin(VersionAdmin):
    list_filter = ["category", "category__team__camp"]
    list_display = ["headline"]


class InfoItemInlineAdmin(admin.StackedInline):
    model = InfoItem
    list_filter = ["category", "category__team__camp"]
    list_display = ["headline"]


@admin.register(InfoCategory)
class InfoCategorydmin(admin.ModelAdmin):
    list_filter = ["team__camp"]
    list_display = ["headline"]
    search_fields = ["headline", "body"]
    inlines = [InfoItemInlineAdmin]
