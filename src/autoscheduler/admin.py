from django.contrib import admin, messages

from .models import AutoEvent, AutoSchedule, AutoSlot


@admin.register(AutoSchedule)
class AutoScheduleAdmin(admin.ModelAdmin):
    list_display = ["id", "camp", "event_type", "created", "applied"]
    list_filter = ["camp", "event_type"]

    actions = [
        "create_autoscheduler_objects",
        "calculate",
        "calculate_and_apply",
    ]

    def create_autoscheduler_objects(self, request, queryset):
        for schedule in queryset:
            schedule.create_autoscheduler_objects()
            messages.success(
                request,
                f"created {schedule.events.count()} events and {schedule.slots.count()} slots for schedule {schedule.id}",
            )

    create_autoscheduler_objects.description = "Create autoscheduler objects"

    def calculate(self, request, queryset):
        for schedule in queryset:
            schedule.calculate_autoschedule()
            messages.success(
                request, f"autoschedule calculated OK for schedule {schedule.id}"
            )

    calculate.description = "Calculate autoschedule"

    def autoschedule_apply(self, request, queryset):
        if len(queryset) != 1:
            messages.error(request, "One at a time please")
            return False
        schedule = queryset.get()
        deleted, created = schedule.apply()
        messages.success(
            request,
            "AutoSchedule applied OK - deleted {deleted} EventInstances and created {created} new EventInstances",
        )

    autoschedule_apply.description = "Apply autoschedule"


@admin.register(AutoSlot)
class AutoSlotAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "schedule",
        "venue",
        "starts_at",
        "duration",
        "session",
        "capacity",
    ]
    list_filter = ["schedule", "venue", "starts_at", "duration", "session", "capacity"]


@admin.register(AutoEvent)
class AutoEventAdmin(admin.ModelAdmin):
    list_display = ["id", "schedule", "name", "duration", "tags", "demand"]
    list_filter = ["schedule", "name", "duration", "tags", "demand"]
