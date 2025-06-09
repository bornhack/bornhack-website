from __future__ import annotations

from django.contrib import admin

from .models import Ride


@admin.register(Ride)
class RideModelAdmin(admin.ModelAdmin):
    list_display = ("camp", "user", "from_location", "to_location", "when", "seats")
    list_filter = ("camp", "user")
