from django.contrib import admin

from .models import Ride


@admin.register(Ride)
class RideModelAdmin(admin.ModelAdmin):
    list_display = ("location", "when", "seats", "user")
    list_filter = ("camp", "user")
