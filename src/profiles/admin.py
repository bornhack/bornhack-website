from __future__ import annotations

from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    actions = ["approve_public_credit_names"]

    list_display = [
        "user",
        "name",
        "description",
        "public_credit_name",
        "public_credit_name_approved",
    ]

    list_filter = ["public_credit_name_approved"]

    def approve_public_credit_names(self, request, queryset) -> None:
        for profile in queryset.filter(public_credit_name_approved=False):
            profile.approve_public_credit_name()

    approve_public_credit_names.description = "Approve Public Credit Name(s)"
