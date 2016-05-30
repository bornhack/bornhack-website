from django.contrib import admin

from . import models


@admin.register(models.NewsItem)
class NewsItemModelAdmin(admin.ModelAdmin):
    list_display = ['title', 'public', 'published_at']
    list_filter = ['public']
