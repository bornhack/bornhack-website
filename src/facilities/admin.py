from django.contrib import admin
from django.utils.html import format_html
from leaflet.admin import LeafletGeoAdmin

from .models import Facility, FacilityFeedback, FacilityQuickFeedback, FacilityType


@admin.register(FacilityQuickFeedback)
class FacilityQuickFeedbackAdmin(admin.ModelAdmin):
    pass


@admin.register(FacilityType)
class FacilityTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "responsible_team", "camp"]
    list_filter = ["responsible_team__camp", "responsible_team"]


@admin.register(Facility)
class FacilityAdmin(LeafletGeoAdmin):
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
