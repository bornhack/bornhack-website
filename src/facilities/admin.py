from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html
from leaflet.admin import LeafletGeoAdmin

from .models import Facility
from .models import FacilityFeedback
from .models import FacilityOpeningHours
from .models import FacilityQuickFeedback
from .models import FacilityType


@admin.register(FacilityQuickFeedback)
class FacilityQuickFeedbackAdmin(admin.ModelAdmin):
    pass


@admin.register(FacilityType)
class FacilityTypeAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ["name", "description", "icon", "marker", "responsible_team", "camp"]
    list_filter = ["responsible_team__camp", "icon", "marker", "responsible_team"]


@admin.register(Facility)
class FacilityAdmin(LeafletGeoAdmin):
    display_raw = True
    save_as = True
    list_display = [
        "name",
        "description",
        "facility_type",
        "camp",
        "team",
        "location",
        "feedback_url",
        "feedback_qrcode",
    ]
    list_filter = [
        "facility_type__responsible_team__camp",
        "facility_type",
        "facility_type__responsible_team",
    ]

    def feedback_qrcode(self, obj):
        return format_html("<img src='{}'>", obj.get_feedback_qr(self.request))

    def feedback_url(self, obj):
        return obj.get_feedback_url(self.request)

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request)


@admin.register(FacilityFeedback)
class FacilityFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "facility",
        "quick_feedback",
        "comment",
        "urgent",
        "handled",
    ]
    list_filter = [
        "facility__facility_type__responsible_team__camp",
        "urgent",
        "handled",
        "facility__facility_type",
        "facility__facility_type__responsible_team",
        "facility",
    ]


@admin.register(FacilityOpeningHours)
class FacilityOpeningHoursAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ["facility", "when", "notes"]
    list_filter = ["facility"]
