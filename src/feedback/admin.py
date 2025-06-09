from __future__ import annotations

from django.contrib import admin
from django.utils import timezone

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "camp", "feedback", "processed_at", "processed_by")
    list_filter = ["processed_at"]
    readonly_fields = ["user", "camp", "feedback", "processed_at", "processed_by"]

    actions = ["mark_as_processed"]

    @admin.action(description="Mark this feedback as processed")
    def mark_as_processed(self, request, queryset) -> None:
        queryset.update(
            processed_at=timezone.now(),
            processed_by=request.user,
        )
