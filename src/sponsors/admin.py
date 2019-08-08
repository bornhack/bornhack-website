from django.contrib import admin

from .models import Sponsor, SponsorTier


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ("name", "tier", "ticket_email", "ticket_ready", "tickets_sent")
    list_filter = ("tier__camp",)


@admin.register(SponsorTier)
class SponsorTierAdmin(admin.ModelAdmin):
    list_display = ("name", "camp", "weight")
    list_editable = ("weight",)
    list_filter = ("camp",)
    ordering = ("weight",)
