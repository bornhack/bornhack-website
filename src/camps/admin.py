from django.contrib import admin

from . import models


@admin.register(models.Camp)
class CampModelAdmin(admin.ModelAdmin):
    pass
