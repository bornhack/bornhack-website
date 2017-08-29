from django.contrib import (
    admin,
    messages
)
from django.core.exceptions import ValidationError


from .models import (
    Event,
    Speaker,
    EventType,
    EventInstance,
    EventLocation,
    SpeakerProposal,
    EventProposal,
    Favorite
)


@admin.register(SpeakerProposal)
class SpeakerProposalAdmin(admin.ModelAdmin):
    def mark_speakerproposal_as_approved(self, request, queryset):
        for sp in queryset:
            sp.mark_as_approved()
    mark_speakerproposal_as_approved.description = 'Approve and create Speaker object(s)'

    actions = ['mark_speakerproposal_as_approved']
    list_filter = ('camp', 'proposal_status', 'user')


@admin.register(EventProposal)
class EventProposalAdmin(admin.ModelAdmin):
    def mark_eventproposal_as_approved(self, request, queryset):
        for ep in queryset:
            if not ep.speakers.all():
                messages.error(
                    request,
                    'Event cant be approved as it has no speaker(s).'
                )
                return False
            else:
                try:
                    ep.mark_as_approved()
                except ValidationError as e:
                    messages.error(request, e)
                    return False
    mark_eventproposal_as_approved.description = 'Approve and create Event object(s)'

    actions = ['mark_eventproposal_as_approved']
    list_filter = ('camp', 'proposal_status', 'user')
    list_display = ('title', 'proposal_status', 'user')


@admin.register(EventLocation)
class EventLocationAdmin(admin.ModelAdmin):
    list_filter = ('camp',)
    list_display = ('name', 'camp')


@admin.register(EventInstance)
class EventInstanceAdmin(admin.ModelAdmin):
    pass


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_filter = ('camp',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    raw_id_fields = ('event_instance',)


class SpeakerInline(admin.StackedInline):
    model = Speaker.events.through


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_filter = ('camp', 'speakers')
    list_display = [
        'title',
        'event_type',
    ]

    inlines = [
        SpeakerInline
    ]
