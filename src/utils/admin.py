from __future__ import annotations

from django.contrib import admin

from .models import OutgoingEmail


@admin.register(OutgoingEmail)
class OutgoingEmailAdmin(admin.ModelAdmin):
    model = OutgoingEmail
    list_display = ["subject", "to_recipients", "processed", "hold", "responsible_team"]
    list_filter = ["processed", "hold", "responsible_team"]
    actions = ["hold_emails", "release_emails"]

    def hold_emails(self, request, queryset):
        for email in queryset.filter(hold=False, processed=False):
            email.hold = True
            email.save()

    hold_emails.description = "Mark these emails with hold=True"

    def release_emails(self, request, queryset):
        for email in queryset.filter(hold=True, processed=False):
            email.hold = False
            email.save()

    release_emails.description = "Mark these emails with hold=False"
