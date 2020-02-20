from django.contrib import admin

from .models import Facility, FacilityFeedback, FacilityQuickFeedback, FacilityType


@admin.register(FacilityQuickFeedback)
class FacilityQuickFeedbackAdmin(admin.ModelAdmin):
    pass


@admin.register(FacilityType)
class FacilityTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "responsible_team", "camp"]
    list_filter = ["responsible_team__camp", "responsible_team"]


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "facility_type", "camp", "team"]
    list_filter = [
        "facility_type__responsible_team__camp",
        "facility_type",
        "facility_type__responsible_team",
    ]


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
