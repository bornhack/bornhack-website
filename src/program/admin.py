from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import (
    Event,
    EventFeedback,
    EventInstance,
    EventLocation,
    EventProposal,
    EventSession,
    EventTrack,
    EventType,
    Favorite,
    Speaker,
    SpeakerAvailability,
    SpeakerProposal,
    SpeakerProposalAvailability,
    Url,
    UrlType,
)


@admin.register(SpeakerProposalAvailability)
class SpeakerProposalAvailabilityAdmin(admin.ModelAdmin):
    list_display = ["speakerproposal", "available", "when"]
    list_filter = ["speakerproposal__camp", "available", "speakerproposal"]


@admin.register(SpeakerAvailability)
class SpeakerAvailabilityAdmin(admin.ModelAdmin):
    list_display = ["speaker", "available", "when"]
    list_filter = ["speaker__camp", "available", "speaker"]
    readonly_fields = ["speaker"]


@admin.register(SpeakerProposal)
class SpeakerProposalAdmin(admin.ModelAdmin):
    def mark_speakerproposal_as_approved(self, request, queryset):
        for sp in queryset:
            sp.mark_as_approved(request)

    mark_speakerproposal_as_approved.description = (
        "Approve and create Speaker object(s)"
    )

    actions = ["mark_speakerproposal_as_approved"]
    list_filter = ("camp", "proposal_status", "user")


def get_speakers_string(event_proposal):
    return ", ".join(event_proposal.speakers.all().values_list("email", flat=True))


get_speakers_string.short_description = "Speakers"


@admin.register(EventProposal)
class EventProposalAdmin(admin.ModelAdmin):
    def mark_eventproposal_as_approved(self, request, queryset):
        for ep in queryset:
            if not ep.speakers.all():
                messages.error(
                    request, "Event cant be approved as it has no speaker(s)."
                )
                return False
            else:
                try:
                    ep.mark_as_approved(request)
                except ValidationError as e:
                    messages.error(request, e)
                    return False

    mark_eventproposal_as_approved.description = "Approve and create Event object(s)"

    def get_speakers(self):
        return

    actions = ["mark_eventproposal_as_approved"]
    list_filter = ("event_type", "proposal_status", "track", "user")
    list_display = ["title", get_speakers_string, "event_type", "proposal_status"]


@admin.register(EventLocation)
class EventLocationAdmin(admin.ModelAdmin):
    list_filter = ("camp",)
    list_display = ("name", "camp", "capacity")


@admin.register(EventTrack)
class EventTrackAdmin(admin.ModelAdmin):
    list_filter = ("camp",)
    list_display = ("name", "camp")


@admin.register(EventSession)
class EventSessionAdmin(admin.ModelAdmin):
    list_display = ("camp", "event_type", "event_location", "when")
    list_filter = ("camp", "event_type", "event_location")
    search_fields = ["event__type", "event__location"]


@admin.register(EventInstance)
class EventInstanceAdmin(admin.ModelAdmin):
    list_display = ("event", "when", "location", "autoscheduled")
    list_filter = ("event__track__camp", "event", "autoscheduled")
    search_fields = ["event__title"]


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_filter = ("camp",)
    readonly_fields = ["proposal", "camp"]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    raw_id_fields = ("event_instance",)


class SpeakerInline(admin.StackedInline):
    model = Speaker.events.through


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "event_type", "duration_minutes", "demand"]
    list_filter = ("track", "event_type", "speakers")

    inlines = [SpeakerInline]

    readonly_fields = ["proposal"]


@admin.register(UrlType)
class UrlTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Url)
class UrlAdmin(admin.ModelAdmin):
    pass


@admin.register(EventFeedback)
class EventFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        "camp",
        "user",
        "event",
        "expectations_fulfilled",
        "attend_speaker_again",
        "rating",
        "created",
        "updated",
        "approved",
        "comment",
    ]
    list_filter = [
        "event__track__camp",
        "expectations_fulfilled",
        "attend_speaker_again",
        "rating",
        "approved",
    ]
    search_fields = ["event__title", "user__username"]
