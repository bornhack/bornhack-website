from django.contrib import admin

from .models import Ride


@admin.register(Ride)
class RideModelAdmin(admin.ModelAdmin):
    list_filter = ('camp', 'user')
