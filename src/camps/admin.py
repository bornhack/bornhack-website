from __future__ import annotations

from django.contrib import admin

from . import models


@admin.register(models.Camp)
class CampModelAdmin(admin.ModelAdmin):
    list_display = ["pk", "title", "camp", "read_only"]
