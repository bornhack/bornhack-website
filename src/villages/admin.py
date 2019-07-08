from django.contrib import admin

from .models import Village


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ["name", "camp", "private", "deleted"]

    list_filter = ["camp", "private", "deleted"]
