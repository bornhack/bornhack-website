from django.contrib import admin

from .models import Event, Speaker, EventType, EventInstance, EventLocation, SpeakerSubmission, EventSubmission


@admin.register(SpeakerSubmission)
class SpeakerSubmissionAdmin(admin.ModelAdmin):
    pass


@admin.register(EventSubmission)
class EventSubmissionAdmin(admin.ModelAdmin):
    pass


@admin.register(EventLocation)
class EventLocationAdmin(admin.ModelAdmin):
    pass


@admin.register(EventInstance)
class EventInstanceAdmin(admin.ModelAdmin):
    pass


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    pass


class SpeakerInline(admin.StackedInline):
    model = Speaker.events.through


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'event_type',
    ]

    inlines = [
        SpeakerInline
    ]
