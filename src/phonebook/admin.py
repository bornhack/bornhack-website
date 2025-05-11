from __future__ import annotations

from django.contrib import admin

from .models import DectRegistration


@admin.register(DectRegistration)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "camp",
        "user",
        "number",
        "letters",
        "description",
        "activation_code",
        "publish_in_phonebook",
    ]
    list_filter = ["camp", "publish_in_phonebook", "user"]
