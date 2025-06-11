from __future__ import annotations

from django.contrib import admin

from .models import Sponsor
from .models import SponsorTier


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "tier",
        "ticket_email",
        "ticket_ready",
        "tickets_sent",
        "tickets_generated",
    )
    list_filter = ("tier__camp",)
    save_as = True


@admin.register(SponsorTier)
class SponsorTierAdmin(admin.ModelAdmin):
    list_display = ("name", "camp", "weight", "week_tickets", "oneday_tickets")
    list_editable = ("weight",)
    list_filter = ("camp",)
    ordering = ("weight",)
    save_as = True
