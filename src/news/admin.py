from __future__ import annotations

from django.contrib import admin

from . import models


@admin.register(models.NewsItem)
class NewsItemModelAdmin(admin.ModelAdmin):
    list_display = ["title", "published_at", "archived"]
    actions = ["archive_news_items", "unarchive_news_items"]

    def archive_news_items(self, request, queryset):
        queryset.filter(archived=False).update(archived=True)

    archive_news_items.description = "Mark newsitem(s) as archived"

    def unarchive_news_items(self, request, queryset):
        queryset.filter(archived=True).update(archived=False)

    unarchive_news_items.description = "Mark newsitem(s) as not archived"
