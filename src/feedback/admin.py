from __future__ import annotations

from django.contrib import admin
from django.utils import timezone

from .models import CampFeedback


@admin.register(CampFeedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "camp", "feedback", "state", "processed_at", "processed_by")
    list_filter = ["processed_at"]
    readonly_fields = ["user", "camp", "feedback", "state", "processed_at", "processed_by"]

    actions = [
        "mark_as_reviewed",
        "mark_as_spam"
    ]

    @admin.action(description="Mark this feedback as reviewed")
    def mark_as_reviewed(self, request, queryset) -> None:
        queryset.update(
            processed_at=timezone.now(),
            processed_by=request.user,
            state="reviewed",
        )

    @admin.action(description="Mark this feedback as spam")
    def mark_as_spam(self, request, queryset) -> None:
        queryset.update(
            processed_at=timezone.now(),
            processed_by=request.user,
            state="spam",
        )
