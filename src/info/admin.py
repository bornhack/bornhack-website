from __future__ import annotations

from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import InfoCategory
from .models import InfoItem


@admin.register(InfoItem)
class InfoItemAdmin(VersionAdmin):
    save_as = True
    list_filter = ["category", "category__team__camp"]
    list_display = ["headline"]


class InfoItemInlineAdmin(admin.StackedInline):
    model = InfoItem
    list_filter = ["category", "category__team__camp"]
    list_display = ["headline"]


@admin.register(InfoCategory)
class InfoCategoryAdmin(admin.ModelAdmin):
    save_as = True
    list_filter = ["team__camp"]
    list_display = ["headline", "team"]
    search_fields = ["headline", "body"]
    inlines = [InfoItemInlineAdmin]
