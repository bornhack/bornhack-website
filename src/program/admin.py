from django.contrib import admin

from .models import Event, Speaker, EventType, EventInstance, EventLocation, SpeakerProposal, EventProposal


@admin.register(SpeakerProposal)
class SpeakerProposalAdmin(admin.ModelAdmin):
    def mark_speakerproposal_as_approved(self, request, queryset):
        for sp in queryset:
            sp.mark_as_approved()
    mark_speakerproposal_as_approved.description = 'Approve and create Speaker object(s)'

    actions = ['mark_speakerproposal_as_approved']


@admin.register(EventProposal)
class EventProposalAdmin(admin.ModelAdmin):
    def mark_eventproposal_as_approved(self, request, queryset):
        for ep in queryset:
            ep.mark_as_approved()
    mark_eventproposal_as_approved.description = 'Approve and create Event object(s)'

    actions = ['mark_eventproposal_as_approved']


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
