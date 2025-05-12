"""Admin config for Village."""
from __future__ import annotations

from django.contrib import admin

from .models import Village


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    """Admin config for Village."""
    list_display = ("name", "camp", "private", "approved", "deleted")
    list_filter = ("camp", "private", "approved", "deleted")
