from django.contrib import admin

from .models import Village


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'private',
        'deleted',
    ]

    list_filter = [
        'private',
        'deleted',
    ]
