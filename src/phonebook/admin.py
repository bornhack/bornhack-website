"""Django admin for phonebook application."""

from __future__ import annotations

from typing import ClassVar

from django.contrib import admin

from .models import DectRegistration


@admin.register(DectRegistration)
class DectRegistrationAdmin(admin.ModelAdmin):
    """Django admin for DECT Registrations."""

    list_display: ClassVar[list[str]] = [
        "camp",
        "user",
        "number",
        "letters",
        "description",
        "activation_code",
        "publish_in_phonebook",
    ]
    list_filter: ClassVar[list[str]] = ["camp", "publish_in_phonebook", "user"]
