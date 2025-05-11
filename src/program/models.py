from __future__ import annotations

import logging
import uuid
from datetime import timedelta

import icalendar
from conference_scheduler import resources
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib.postgres.fields import RangeOperators
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import F
from django.db.models import Q
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django_prometheus.models import ExportModelOperationsMixin
from psycopg2.extras import DateTimeTZRange
from taggit.managers import TaggableManager

from utils.database import CastToInteger
from utils.models import CampRelatedModel
from utils.models import CreatedUpdatedModel
from utils.models import UUIDModel
from utils.models import UUIDTaggedItem
from utils.slugs import unique_slugify

from .email import add_event_proposal_accepted_email
from .email import add_event_proposal_rejected_email
from .email import add_speaker_proposal_accepted_email
from .email import add_speaker_proposal_rejected_email

logger = logging.getLogger("bornhack.%s" % __name__)


class UrlType(ExportModelOperationsMixin("url_type"), CreatedUpdatedModel):
    """Each Url object has a type."""

    name = models.CharField(
        max_length=25,
        help_text="The name of this type",
        unique=True,
    )

    icon = models.CharField(
        max_length=100,
        default="fas fa-link",
        help_text="Name of the fontawesome icon to use, including the 'fab fa-' or 'fas fa-' part.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Url(ExportModelOperationsMixin("url"), CampRelatedModel):
    """This model contains URLs related to
    - SpeakerProposals
    - EventProposals
    - Speakers
    - Events
    Each URL has a UrlType and a ForeignKey to the model to which it belongs.
    When a SpeakerProposal or EventProposal is approved the related URLs will
    be copied with FK to the new Speaker/Event objects.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    url = models.URLField(help_text="The actual URL")

    url_type = models.ForeignKey(
        "program.UrlType",
        help_text="The type of this URL",
        on_delete=models.PROTECT,
    )

    speaker_proposal = models.ForeignKey(
        "program.SpeakerProposal",
        null=True,
        blank=True,
        help_text="The speaker proposal object this URL belongs to",
        on_delete=models.CASCADE,
        related_name="urls",
    )

    event_proposal = models.ForeignKey(
        "program.EventProposal",
        null=True,
        blank=True,
        help_text="The event proposal object this URL belongs to",
        on_delete=models.CASCADE,
        related_name="urls",
    )

    speaker = models.ForeignKey(
        "program.Speaker",
        null=True,
        blank=True,
        help_text="The speaker proposal object this URL belongs to",
        on_delete=models.CASCADE,
        related_name="urls",
    )

    event = models.ForeignKey(
        "program.Event",
        null=True,
        blank=True,
        help_text="The event proposal object this URL belongs to",
        on_delete=models.CASCADE,
        related_name="urls",
    )

    def __str__(self):
        return self.url

    def clean_fk(self):
        """Make sure we have exactly one FK"""
        fks = 0
        if self.speaker_proposal:
            fks += 1
        if self.event_proposal:
            fks += 1
        if self.speaker:
            fks += 1
        if self.event:
            fks += 1
        if fks != 1:
            raise ValidationError(
                f"Url objects must have exactly one FK, this has {fks}",
            )

    def save(self, *args, **kwargs):
        """Just clean_fk() and super save()."""
        self.clean_fk()
        super().save(*args, **kwargs)

    @property
    def owner(self):
        """Return the object this Url belongs to"""
        if self.speaker_proposal:
            return self.speaker_proposal
        if self.event_proposal:
            return self.event_proposal
        if self.speaker:
            return self.speaker
        if self.event:
            return self.event
        return None

    @property
    def camp(self):
        return self.owner.camp

    camp_filter = [
        "speaker_proposal__camp",
        "event_proposal__track__camp",
        "speaker__camp",
        "event__track__camp",
    ]


###############################################################################


class Availability(CampRelatedModel, UUIDModel):
    """This model contains all the availability info for speaker_proposals and
    speakers. It is inherited by SpeakerProposalAvailability and SpeakerAvailability
    models.
    """

    class Meta:
        abstract = True

    when = DateTimeRangeField(
        db_index=True,
        help_text="The period when this speaker is available or unavailable. Must be 1 hour!",
    )

    available = models.BooleanField(
        db_index=True,
        help_text="Is the speaker available or unavailable during this hour? Check for available, uncheck for unavailable.",
    )


class SpeakerProposalAvailability(
    ExportModelOperationsMixin("speaker_proposal_availability"),
    Availability,
):
    """Availability info for SpeakerProposal objects"""

    class Meta:
        """Add ExclusionConstraints preventing overlaps and adjacent ranges with same availability"""

        constraints = [
            # we do not want overlapping ranges
            ExclusionConstraint(
                name="prevent_speaker_proposal_availability_overlaps",
                expressions=[
                    (F("speaker_proposal"), RangeOperators.EQUAL),
                    ("when", RangeOperators.OVERLAPS),
                ],
            ),
            # we do not want adjacent ranges with same availability
            ExclusionConstraint(
                name="prevent_speaker_proposal_availability_adjacent_mergeable",
                expressions=[
                    ("speaker_proposal", RangeOperators.EQUAL),
                    (CastToInteger("available"), RangeOperators.EQUAL),
                    ("when", RangeOperators.ADJACENT_TO),
                ],
            ),
        ]

    speaker_proposal = models.ForeignKey(
        "program.SpeakerProposal",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="availabilities",
        help_text="The speaker proposal object this availability belongs to",
    )

    @property
    def camp(self):
        return self.speaker_proposal.camp

    camp_filter = "speaker_proposal__camp"

    def clean(self):
        if SpeakerProposalAvailability.objects.filter(
            speaker_proposal=self.speaker_proposal,
            when__adjacent_to=self.when,
            available=self.available,
        ).exists():
            raise ValidationError(
                f"An adjacent SpeakerProposalAvailability object for this SpeakerProposal already exists with the same value for available, cannot save() {self.when}",
            )

    def __str__(self):
        return f"SpeakerProposalAvailability: {self.speaker_proposal.name} is {'not ' if not self.available else ''}available from {self.when.lower} to {self.when.upper}"


class SpeakerAvailability(
    ExportModelOperationsMixin("speaker_availability"),
    Availability,
):
    """Availability info for Speaker objects"""

    class Meta:
        """Add ExclusionConstraints preventing overlaps and adjacent ranges with same availability"""

        constraints = [
            # we do not want overlapping ranges
            ExclusionConstraint(
                name="prevent_speaker_availability_overlaps",
                expressions=[
                    (F("speaker"), RangeOperators.EQUAL),
                    ("when", RangeOperators.OVERLAPS),
                ],
            ),
            # we do not want adjacent ranges with same availability
            ExclusionConstraint(
                name="prevent_speaker_availability_adjacent_mergeable",
                expressions=[
                    ("speaker", RangeOperators.EQUAL),
                    (CastToInteger("available"), RangeOperators.EQUAL),
                    ("when", RangeOperators.ADJACENT_TO),
                ],
            ),
        ]

    speaker = models.ForeignKey(
        "program.Speaker",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="availabilities",
        help_text="The speaker object this availability belongs to (if any)",
    )

    @property
    def camp(self):
        return self.speaker.camp

    camp_filter = "speaker__camp"

    def clean(self):
        # this should be an ExclusionConstraint but the boolean condition isn't conditioning :/
        if SpeakerAvailability.objects.filter(
            speaker=self.speaker,
            when__adjacent_to=self.when,
            available=self.available,
        ).exists():
            raise ValidationError(
                "An adjacent SpeakerAvailability object for this Speaker already exists with the same value for available, cannot save()",
            )


###############################################################################


class UserSubmittedModel(CampRelatedModel):
    """An abstract model containing the stuff that is shared
    between the SpeakerProposal and EventProposal models.
    """

    class Meta:
        abstract = True

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)

    PROPOSAL_PENDING = "pending"
    PROPOSAL_APPROVED = "approved"
    PROPOSAL_REJECTED = "rejected"

    PROPOSAL_STATUSES = [PROPOSAL_PENDING, PROPOSAL_APPROVED, PROPOSAL_REJECTED]

    PROPOSAL_STATUS_CHOICES = [
        (PROPOSAL_PENDING, "Pending approval"),
        (PROPOSAL_APPROVED, "Approved"),
        (PROPOSAL_REJECTED, "Rejected"),
    ]

    proposal_status = models.CharField(
        max_length=50,
        choices=PROPOSAL_STATUS_CHOICES,
        default=PROPOSAL_PENDING,
    )

    reason = models.TextField(
        blank=True,
        help_text="The reason this proposal was accepted or rejected. This text will be included in the email to the submitter. Leave blank to send a standard email.",
    )

    def __str__(self):
        return f"{self.headline} (submitted by: {self.user}, status: {self.proposal_status})"

    def save(self, **kwargs):
        if not self.camp.call_for_participation_open:
            message = "Call for participation is not open"
            if hasattr(self, "request"):
                messages.error(self.request, message)
            raise ValidationError(message)
        super().save(**kwargs)

    def delete(self, **kwargs):
        if not self.camp.call_for_participation_open:
            message = "Call for participation is not open"
            if hasattr(self, "request"):
                messages.error(self.request, message)
            raise ValidationError(message)
        super().delete(**kwargs)


class SpeakerProposal(
    ExportModelOperationsMixin("speaker_proposal"),
    UserSubmittedModel,
):
    """A speaker proposal"""

    camp = models.ForeignKey(
        "camps.Camp",
        related_name="speaker_proposals",
        on_delete=models.PROTECT,
        editable=False,
    )

    name = models.CharField(
        max_length=150,
        help_text="Name or alias of the speaker/artist/host",
    )

    email = models.EmailField(
        blank=True,
        max_length=150,
        help_text="The email of the speaker/artist/host. Defaults to the logged in users email if empty.",
    )

    biography = models.TextField(
        help_text="Biography of the speaker/artist/host. Markdown is supported.",
    )

    submission_notes = models.TextField(
        help_text="Private notes for this speaker/artist/host. Only visible to the submitting user and the BornHack organisers.",
        blank=True,
    )

    needs_oneday_ticket = models.BooleanField(
        default=False,
        help_text="Check if BornHack needs to provide a free one-day ticket for this speaker",
    )

    event_conflicts = models.ManyToManyField(
        "program.Event",
        related_name="speaker_proposal_conflicts",
        blank=True,
        help_text="Pick the Events this person wishes to attend, and we will attempt to avoid scheduling conflicts.",
    )

    @property
    def headline(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy(
            "program:speaker_proposal_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.uuid},
        )

    def mark_as_approved(self, request=None):
        """Marks a SpeakerProposal as approved, including creating/updating the related Speaker object"""
        speaker_proposalmodel = apps.get_model("program", "SpeakerProposal")
        # create a Speaker if we don't have one
        if not hasattr(self, "speaker"):
            speakermodel = apps.get_model("program", "Speaker")
            speaker = speakermodel()
            speaker.proposal = self
        else:
            # this proposal has been approved before, update the existing speaker
            speaker = self.speaker

        # set Speaker data
        speaker.camp = self.camp
        speaker.email = self.email if self.email else self.user.email
        speaker.name = self.name
        speaker.biography = self.biography
        speaker.needs_oneday_ticket = self.needs_oneday_ticket
        speaker.save()

        # save speaker availability, start with a clean slate
        speaker.availabilities.all().delete()
        for availability in self.availabilities.all():
            SpeakerAvailability.objects.create(
                speaker=speaker,
                when=availability.when,
                available=availability.available,
            )

        # mark as approved and save
        self.proposal_status = speaker_proposalmodel.PROPOSAL_APPROVED
        self.save()

        # copy all the URLs to the speaker object
        speaker.urls.clear()
        for url in self.urls.all():
            Url.objects.create(url=url.url, url_type=url.url_type, speaker=speaker)

        # copy event conflicts to the speaker object
        speaker.event_conflicts.clear()
        speaker.event_conflicts.set(self.event_conflicts.all())

        # a message to the admin (if we have a request)
        if request:
            messages.success(
                request,
                "Speaker object %s has been created/updated" % speaker,
            )
        add_speaker_proposal_accepted_email(self)

    def mark_as_rejected(self, request=None):
        speaker_proposalmodel = apps.get_model("program", "SpeakerProposal")
        self.proposal_status = speaker_proposalmodel.PROPOSAL_REJECTED
        self.save()
        if request:
            messages.success(
                request,
                "SpeakerProposal %s has been rejected" % self.name,
            )
        add_speaker_proposal_rejected_email(self)

    @property
    def event_types(self):
        """Return a queryset of the EventType objects for the EventProposals"""
        return EventType.objects.filter(
            id__in=self.event_proposals.all().values_list("event_type", flat=True),
        )

    @property
    def title(self):
        """Convenience method to return the proper host_title"""
        if self.event_proposals.values_list("event_type").distinct().count() != 1:
            # we have no events, or events of different eventtypes, use generic title
            return "Person"
        return self.event_proposals.first().event_type.host_title


class EventProposal(ExportModelOperationsMixin("event_proposal"), UserSubmittedModel):
    """An event proposal"""

    track = models.ForeignKey(
        "program.EventTrack",
        related_name="event_proposals",
        help_text="The track this event belongs to",
        on_delete=models.PROTECT,
    )

    title = models.CharField(
        max_length=255,
        help_text="The title of this event. Keep it short and memorable.",
    )

    abstract = models.TextField(
        help_text="The abstract for this event. Describe what the audience can expect to see/hear.",
    )

    event_type = models.ForeignKey(
        "program.EventType",
        help_text="The type of event",
        on_delete=models.PROTECT,
        related_name="event_proposals",
    )

    speakers = models.ManyToManyField(
        "program.SpeakerProposal",
        blank=True,
        help_text="Pick the speaker(s) for this event. If you cannot see anything here you need to go back and create Speaker Proposal(s) first.",
        related_name="event_proposals",
    )

    allow_video_recording = models.BooleanField(
        default=False,
        help_text="Recordings are made available under the <b>CC BY-SA 4.0</b> license. Uncheck if you do not want the event recorded, or if you cannot accept the license.",
    )

    allow_video_streaming = models.BooleanField(
        default=False,
        help_text="Uncheck if you do not want the event live streamed.",
    )

    duration = models.IntegerField(
        blank=True,
        help_text="How much time (in minutes) should we set aside for this event?",
    )

    submission_notes = models.TextField(
        help_text="Private notes for this event. Only visible to the submitting user and the BornHack organisers.",
        blank=True,
    )

    use_provided_speaker_laptop = models.BooleanField(
        help_text="Will you be using the provided speaker laptop?",
        default=True,
    )

    tags = TaggableManager(
        through=UUIDTaggedItem,
        blank=True,
    )

    @property
    def camp(self):
        return self.track.camp

    camp_filter = "track__camp"

    @property
    def headline(self):
        return self.title

    def save(self, **kwargs):
        if not self.duration:
            self.duration = self.event_type.event_duration_minutes
        super().save(**kwargs)

    def get_absolute_url(self):
        return reverse_lazy(
            "program:event_proposal_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.uuid},
        )

    def get_available_speaker_proposals(self):
        """Return all SpeakerProposals submitted by the user who submitted this EventProposal,
        which are not already added to this EventProposal
        """
        return SpeakerProposal.objects.filter(
            camp=self.track.camp,
            user=self.user,
        ).exclude(uuid__in=self.speakers.all().values_list("uuid"))

    def mark_as_approved(self, request=None):
        eventmodel = apps.get_model("program", "Event")
        event_proposalmodel = apps.get_model("program", "EventProposal")
        # use existing event if we have one
        if not hasattr(self, "event"):
            event = eventmodel()
        else:
            event = self.event
        event.track = self.track
        event.title = self.title
        event.abstract = self.abstract
        event.event_type = self.event_type
        event.proposal = self
        event.video_recording = self.allow_video_recording
        event.video_streaming = self.allow_video_streaming
        event.save()
        # loop through the speaker_proposals linked to this event_proposal and associate any related speaker objects with this event
        for sp in self.speakers.all():
            if sp.proposal_status != "approved":
                raise ValidationError("Not all speakers are approved or created yet.")
            event.speakers.add(sp.speaker)

        self.proposal_status = event_proposalmodel.PROPOSAL_APPROVED
        self.save()

        # clear any old urls from the event object and copy all the URLs from the proposal
        event.urls.clear()
        for url in self.urls.all():
            Url.objects.create(url=url.url, url_type=url.url_type, event=event)

        # set event tags
        event.tags.add(*self.tags.names())

        if request:
            messages.success(
                request,
                "Event object %s has been created/updated" % event,
            )
        add_event_proposal_accepted_email(self)

    def mark_as_rejected(self, request=None):
        event_proposalmodel = apps.get_model("program", "EventProposal")
        self.proposal_status = event_proposalmodel.PROPOSAL_REJECTED
        self.save()
        if request:
            messages.success(request, "EventProposal %s has been rejected" % self.title)
        add_event_proposal_rejected_email(self)

    @property
    def can_be_approved(self):
        """We cannot approve an EventProposal until all SpeakerProposals are approved"""
        if self.speakers.exclude(proposal_status="approved").exists():
            return False
        return True


###############################################################################


class EventTrack(ExportModelOperationsMixin("event_track"), CampRelatedModel):
    """All events belong to a track. Administration of a track can be delegated to one or more users."""

    name = models.CharField(max_length=100, help_text="The name of this Track")

    slug = models.SlugField(help_text="The url slug for this Track")

    camp = models.ForeignKey(
        "camps.Camp",
        related_name="event_tracks",
        on_delete=models.PROTECT,
        help_text="The Camp this Track belongs to",
    )

    managers = models.ManyToManyField(
        "auth.User",
        related_name="managed_tracks",
        blank=True,
        help_text="If this track is managed by someone other than the Content team pick the users here.",
    )

    def __str__(self):
        return f"{self.name} ({self.camp.title})"

    class Meta:
        unique_together = (("camp", "slug"), ("camp", "name"))

    def serialize(self):
        return {"name": self.name, "slug": self.slug}


class EventLocation(ExportModelOperationsMixin("event_location"), CampRelatedModel):
    """The places where stuff happens"""

    name = models.CharField(max_length=100)

    slug = models.SlugField()

    icon = models.CharField(
        max_length=100,
        help_text="Name of the fontawesome icon to use without the 'fa-' part",
    )

    camp = models.ForeignKey(
        "camps.Camp",
        related_name="event_locations",
        on_delete=models.PROTECT,
    )

    capacity = models.PositiveIntegerField(
        default=20,
        help_text="The capacity of this location. Used by the autoscheduler.",
    )

    conflicts = models.ManyToManyField(
        "self",
        blank=True,
        help_text="Select the locations which this location conflicts with. Nothing can be scheduled in a location if a conflicting location has a scheduled Event at the same time. Example: If one room can be split into two, then the big room would conflict with each of the two small rooms (but the small rooms would not conflict with eachother).",
    )

    def __str__(self):
        return f"{self.name} ({self.camp})"

    class Meta:
        unique_together = (("camp", "slug"), ("camp", "name"))

    def save(self, **kwargs):
        """Create a slug"""
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                self.__class__.objects.filter(camp=self.camp).values_list(
                    "slug",
                    flat=True,
                ),
            )
        super().save(**kwargs)

    def serialize(self):
        return {"name": self.name, "slug": self.slug, "icon": self.icon}

    @property
    def icon_html(self):
        return mark_safe(f'<i class="fas fa-{self.icon} fa-fw"></i>')

    @property
    def event_slots(self):
        return self.camp.event_slots.filter(event_session__event_location=self)

    def scheduled_event_slots(self):
        """Returns a QuerySet of all EventSlots scheduled in this EventLocation"""
        return self.event_slots.filter(event__isnull=False)

    def is_available(self, when, ignore_event_slot_ids=None):
        """A location is available if nothing is scheduled in it at that time"""
        ignore_event_slot_ids = ignore_event_slot_ids or []
        if (
            self.event_slots.filter(event__isnull=False, when__overlap=when)
            .exclude(pk__in=ignore_event_slot_ids)
            .exists()
        ):
            # something is scheduled, the location is not available at this time
            return False
        # nothing is scheduled, location is available
        return True


class EventType(ExportModelOperationsMixin("event_type"), CreatedUpdatedModel):
    """Every event needs to have a type."""

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of this event type",
    )

    slug = models.SlugField()

    description = models.TextField(
        default="",
        help_text="The description of this type of event. Used in content submission flow.",
        blank=True,
    )

    color = models.CharField(
        max_length=50,
        help_text="The background color of this event type",
    )

    light_text = models.BooleanField(
        default=False,
        help_text="Check if this event type should use white text color",
    )

    icon = models.CharField(
        max_length=25,
        help_text="Name of the fontawesome icon to use, without the 'fa-' part",
        default="wrench",
    )

    notifications = models.BooleanField(
        default=False,
        help_text="Check to send notifications for this event type",
    )

    public = models.BooleanField(
        default=False,
        help_text="Check to permit users to submit events of this type",
    )

    include_in_event_list = models.BooleanField(
        default=True,
        help_text="Include events of this type in the event list?",
    )

    host_title = models.CharField(
        max_length=30,
        help_text='What to call someone hosting this type of event. Like "Artist" for Music or "Speaker" for talks.',
        default="Person",
    )

    event_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="The default duration of an event of this type, in minutes. Optional. This default can be overridden in individual EventSessions as needed.",
    )

    support_autoscheduling = models.BooleanField(
        default=False,
        help_text="Check to enable this EventType in the autoscheduler",
    )

    support_speaker_event_conflicts = models.BooleanField(
        default=True,
        help_text="True if Events of this type should be selectable in the EventConflict m2m for SpeakerProposal and Speaker objects.",
    )

    order = models.IntegerField(
        default=0,
        help_text="Order for showing the event type in a list",
    )

    def __str__(self):
        return self.name

    def serialize(self):
        return {
            "name": self.name,
            "slug": self.slug,
            "color": self.color,
            "light_text": self.light_text,
        }

    def clean(self):
        if self.support_autoscheduling and not self.event_duration_minutes:
            raise ValidationError(
                "You must specify event_duration_minutes to support autoscheduling",
            )

    @property
    def duration(self):
        """Just return a timedelta of the lenght of this Session"""
        return timedelta(minutes=self.event_duration_minutes)

    def icon_html(self):
        return mark_safe(
            f'<i class="fas fa-{self.icon} fa-fw" style="color: {self.color};"></i>',
        )

    class Meta:
        ordering = ["order"]


class EventSession(ExportModelOperationsMixin("event_session"), CampRelatedModel):
    """An EventSession define the "opening hours" for an EventType in an EventLocation.

    Creating an EventSession also creates the related EventSlots. Updating an EventSesion
    adds or removes EventSlots as needed.

    Multiple EventSessions can happen at the same time at the same location, for
    example we have both Meetups and Music Acts in the Bar Area in the evenings.

    EventSessions are used to allow submitters to specify speaker availability
    when submitting, and to assist and validate event scheduling (auto and manual).
    """

    class Meta:
        ordering = ["when", "event_type", "event_location"]
        constraints = [
            # We do not want overlapping sessions for the same EventType/EventLocation/duration combo.
            ExclusionConstraint(
                name="prevent_event_session_event_type_event_location_overlaps",
                expressions=[
                    ("when", RangeOperators.OVERLAPS),
                    ("event_location", RangeOperators.EQUAL),
                    ("event_type", RangeOperators.EQUAL),
                    ("event_duration_minutes", RangeOperators.EQUAL),
                ],
            ),
            # we do not want adjacent sessions for the same type and location and duration
            ExclusionConstraint(
                name="prevent_adjacent_eventsessions",
                expressions=[
                    ("event_location", RangeOperators.EQUAL),
                    ("event_type", RangeOperators.EQUAL),
                    ("event_duration_minutes", RangeOperators.EQUAL),
                    ("when", RangeOperators.ADJACENT_TO),
                ],
            ),
        ]

    camp = models.ForeignKey(
        "camps.Camp",
        related_name="event_sessions",
        on_delete=models.PROTECT,
        help_text="The Camp this EventSession belongs to",
    )

    event_type = models.ForeignKey(
        "program.EventType",
        on_delete=models.PROTECT,
        related_name="event_sessions",
        help_text="The type of event this session is for",
    )

    event_location = models.ForeignKey(
        "program.EventLocation",
        on_delete=models.PROTECT,
        related_name="event_sessions",
        help_text="The event location this session is for",
    )

    when = DateTimeRangeField(
        help_text="A period of time where this type of event can be scheduled. Input format is <i>YYYY-MM-DD HH:MM</i>",
    )

    event_duration_minutes = models.PositiveIntegerField(
        blank=True,
        help_text="The duration of events in this EventSession. Defaults to the value from the EventType of this EventSession.",
    )

    description = models.TextField(
        blank=True,
        help_text="Description of this session (optional).",
    )

    def __str__(self):
        return f"EventSession for {self.event_type} in {self.event_location.name}: {self.when}"

    def save(self, **kwargs):
        if not self.event_duration_minutes:
            self.event_duration_minutes = self.event_type.event_duration_minutes
        super().save(**kwargs)

    @property
    def duration(self):
        """Just return a timedelta of the lenght of this Session"""
        return self.when.upper - self.when.lower

    @property
    def free_time(self):
        """Returns a timedelta of the free time in this Session."""
        return self.duration - timedelta(
            minutes=self.event_duration_minutes * self.get_unavailable_slots().count(),
        )

    def get_available_slots(self, count_autoscheduled_as_free=False, bounds="()"):
        """Return a queryset of slots that have nothing scheduled, remember to consider
        conflicting locations too.
        """
        # do we want to count slots with autoscheduled Events as free or not?
        if count_autoscheduled_as_free:
            # a slot is available if nothing is scheduled, or if the event is autoscheduled
            availablefilter = Q(event__isnull=True) | Q(autoscheduled=True)
            # a slot is busy if something is manually scheduled
            busyfilter = Q(autoscheduled=False)
        else:
            # a slot is available if nothing is scheduled
            availablefilter = Q(event__isnull=True)
            # a slot is busy if something is scheduled
            busyfilter = Q(event__isnull=False)

        # get the times of all busy slots in the same or conflicting
        # locations which overlap with this session
        conflict_slot_times = self.camp.event_slots.filter(
            # get slots at the same or a conflicting location
            Q(event_session__event_location__in=self.event_location.conflicts.all())
            | Q(event_session__event_location=self.event_location),
            # which have something scheduled in them
            busyfilter,
            # at the same time as this session
            when__overlap=self.when,
        ).values_list("when", flat=True)

        # build the excludefilter so we exclude any slots that overlap with any
        # of our conflict_slot_times
        excludefilter = Q()
        for slot in conflict_slot_times:
            # slot is a DateTimeTZRange with bounds "[)"
            excludefilter |= Q(when__overlap=slot)

        # do the thing
        return self.event_slots.filter(availablefilter).exclude(excludefilter)

    def get_unavailable_slots(self, count_autoscheduled_as_free=False, bounds="[)"):
        """Return a list of slots that are not available for some reason"""
        return self.event_slots.exclude(
            id__in=self.get_available_slots(
                count_autoscheduled_as_free=count_autoscheduled_as_free,
                bounds=bounds,
            ).values_list("id", flat=True),
        )

    def get_slot_times(self, bounds="[)"):
        """Return a list of the DateTimeTZRanges we want EventSlots to exists for"""
        slots = []
        period = self.when
        duration = timedelta(minutes=self.event_duration_minutes)
        if period.upper - period.lower < duration:
            # this period is shorter than the duration, no slots
            return slots

        # create the first slot
        slot = DateTimeTZRange(period.lower, period.lower + duration, bounds=bounds)

        # loop until we pass the end
        while slot.upper < period.upper:
            slots.append(slot)
            # the next slot starts when this one ends
            slot = DateTimeTZRange(slot.upper, slot.upper + duration, bounds=bounds)

        # append the final slot to the list unless it continues past the end
        if not slot.upper > period.upper:
            slots.append(slot)
        return slots

    def fixup_event_slots(self):
        """This method takes care of creating and deleting EventSlots when the EventSession is created, updated or deleted"""
        # get a set of DateTimeTZRange objects representing the EventSlots we need
        needed_slot_times = set(self.get_slot_times(bounds="[)"))

        # get a set of DateTimeTZRange objects representing the EventSlots we have in DB
        db_slot_times = set(self.event_slots.all().values_list("when", flat=True))

        # loop over and delete unneeded slots
        for slot in db_slot_times.difference(needed_slot_times):
            self.event_slots.get(when=slot).delete()

        # loop over and create missing slots
        for slot in needed_slot_times.difference(db_slot_times):
            self.event_slots.create(event_session=self, when=slot)

    def scheduled_event_slots(self):
        return self.event_slots.filter(event__isnull=False)


class EventSlot(ExportModelOperationsMixin("event_slot"), CampRelatedModel):
    """An EventSlot defines a window where we can schedule an Event.

    The EventType and EventLocation is defined by the EventSession this
    EventSlot belongs to. EventSlots are created and deleted by a post_save
    signal when the parent EventSession is created, updated or deleted.

    If the EventSession has a duration of 6 hours and event_duration_minutes=60
    then 6 instances of this model would exist for that EventSession.
    """

    class Meta:
        ordering = ["when"]
        constraints = [
            # we do not want overlapping slots for the same EventSession
            ExclusionConstraint(
                name="prevent_slot_session_overlaps",
                expressions=[
                    ("when", RangeOperators.OVERLAPS),
                    ("event_session", RangeOperators.EQUAL),
                ],
            ),
        ]

    event_session = models.ForeignKey(
        "program.EventSession",
        related_name="event_slots",
        on_delete=models.PROTECT,
        help_text="The EventSession this EventSlot belongs to",
    )

    when = DateTimeRangeField(
        help_text="Start and end time of this slot",
    )

    event = models.ForeignKey(
        "program.Event",
        null=True,
        blank=True,
        related_name="event_slots",
        on_delete=models.SET_NULL,
        help_text="The Event scheduled in this EventSlot",
    )

    autoscheduled = models.BooleanField(
        blank=True,
        null=True,
        default=None,
        help_text="True if the Event was scheduled by the AutoScheduler, False if it was scheduled manually, None if there is nothing scheduled in this EventSlot.",
    )

    @property
    def camp(self):
        return self.event_session.camp

    camp_filter = "event_session__camp"

    def __str__(self):
        return f"{self.when} ({self.event_session.event_location.name}, {self.event_session.event_type})"

    def clean(self):
        """Validate EventSlot length, time, and autoscheduled status"""
        if self.when.upper - self.when.lower != timedelta(
            minutes=self.event_session.event_duration_minutes,
        ):
            raise ValidationError(
                f"This EventSlot has the wrong length. It must be {self.event_session.event_duration_minutes} minutes long.",
            )

        # remember to use "[)" bounds when comparing
        if self.when not in self.event_session.get_slot_times(bounds="[)"):
            raise ValidationError(
                "This EventSlot is not inside this EventSession, or it might be misaligned",
            )

        # if we have an Event we want to know if it was autoscheduled or not
        if self.event and self.autoscheduled is None:
            raise ValidationError(
                "An EventSlot with a scheduled Event must have autoscheduled set to either True or False, not None",
            )
        self.clean_speakers()
        self.clean_location()

    def get_autoscheduler_slot(self):
        """Return a conference_scheduler.resources.Slot object matching this EventSlot"""
        return resources.Slot(
            venue=self.event_session.event_location.id,
            starts_at=self.when.lower,
            duration=int((self.when.upper - self.when.lower).total_seconds() / 60),
            session=self.event_session.id,
            capacity=self.event_session.event_location.capacity,
        )

    @property
    def event_type(self):
        return self.event_session.event_type

    @property
    def event_location(self):
        return self.event_session.event_location

    def clean_speakers(self):
        """Check if all speakers are available"""
        if self.event:
            for speaker in self.event.speakers.all():
                if not speaker.is_available(
                    when=self.when,
                    ignore_event_slot_ids=[self.pk],
                ):
                    raise ValidationError(
                        f"The speaker {speaker} is not available at this time",
                    )

    def clean_location(self):
        """Make sure the location is available"""
        if self.event:
            if not self.event_location.is_available(
                when=self.when,
                ignore_event_slot_ids=[self.pk],
            ):
                raise ValidationError(
                    f"The location {self.event_location} is not available at this time",
                )

    def unschedule(self):
        """Clear the Event FK and autoscheduled status, removing the Event from the schedule"""
        self.event = None
        self.autoscheduled = None
        self.save()

    @property
    def overflow(self):
        """If we have more demand than capacity return the overflow"""
        if self.event and self.event.demand > self.event_location.capacity:
            return (self.event_location.capacity - self.event.demand) * -1
        return 0

    @property
    def duration(self):
        return self.when.upper - self.when.lower

    @property
    def duration_minutes(self):
        return int(self.duration.total_seconds() // 60)

    def get_ics_event(self):
        if not self.event:
            return False
        ievent = icalendar.Event()
        ievent["summary"] = self.event.title
        domain = Site.objects.get_current().domain
        speakers = ", ".join(self.event.speakers.all().values_list("name", flat=True))
        recorded = "Yes" if self.event.video_recording else "No"
        streamed = "Yes" if self.event.video_streaming else "No"
        ievent["description"] = (
            f"URL: https://{domain}{self.event.get_absolute_url()}\n\n"
            f"Speaker(s): {speakers}\n\n"
            f"Recorded: {recorded}\n\n"
            f"Streamed: {streamed}\n\n"
            f"{self.event.abstract}"
        )
        ievent["dtstart"] = icalendar.vDatetime(self.when.lower).to_ical()
        ievent["dtend"] = icalendar.vDatetime(
            self.when.lower + self.event.duration,
        ).to_ical()
        ievent["dtstamp"] = icalendar.vDatetime(timezone.now()).to_ical()
        ievent["uid"] = self.uuid
        ievent["location"] = icalendar.vText(self.event_location.name)
        return ievent

    def get_absolute_url(self):
        return reverse("program:event_detail", kwargs={"event_slug": self.slug})

    @property
    def uuid(self):
        """Returns a consistent UUID for this EventSlot with this Event (if any).

        We want the UUID to be the same even if this EventSlot is deleted and replaced by
        another at the same start time and location, so it cannot be a regular UUIDField.
        We want the UUID to depend on event, location and start time, meaning if any of
        these change we consider it a "schedule change" and create a new UUID.

        We create the UUID from 32 hex digits, which are the unix timestamp of the starttime,
        the event id, and the location id, and the rest is padded with the event uuid as needed.

        Examples:
            # timestamp=1472374800 location_id=1 event_id=27 event_uuid=748316fa-78a5-4172-850b-341fc41ba2ba
            In [1]: EventSlot.objects.filter(event__isnull=False).first().uuid
            Out[1]: UUID('14723748-0012-7748-316f-a78a54172850')

            # timestamp=1472378400 location_id=3 event_id=0 event_uuid=00000000-0000-0000-0000-000000000000
            In [2]: EventSlot.objects.filter(event__isnull=True).first().uuid
            Out[2]: UUID('14723784-0030-0000-0000-000000000000')
        """
        # get starttime as unix timestamp, 10 bytes (until Sat, Nov. 20th 2286 at 18:46:40 CET)
        start_timestamp = int(self.when.lower.timestamp())

        # get location_id
        location_id = self.event_location.id  # 1-3? bytes

        # do we have an event?
        if self.event:
            event_id = self.event.id  # 1-4? bytes
            event_uuid = str(self.event.uuid).replace("-", "")
        else:
            event_id = 0
            event_uuid = "0" * 32

        # put the start of the UUID together
        uuidbase = f"{start_timestamp}{location_id}{event_id}"

        # pad using event_uuid up to 32 hex chars and return
        return uuid.UUID(f"{uuidbase}{event_uuid[0 : 32 - len(uuidbase)]}")


class Event(ExportModelOperationsMixin("event"), CampRelatedModel):
    """Something that is on the program one or more times."""

    uuid = models.UUIDField(
        default=uuid.uuid4,
        # unique=True,
        editable=False,
        help_text="This field is not the PK of the model. It is used to create EventSlot UUID for FRAB and iCal and other calendaring purposes.",
    )

    title = models.CharField(max_length=255, help_text="The title of this event")

    abstract = models.TextField(help_text="The abstract for this event")

    event_type = models.ForeignKey(
        "program.EventType",
        help_text="The type of this event",
        related_name="events",
        on_delete=models.PROTECT,
    )

    slug = models.SlugField(
        blank=True,
        max_length=255,
        help_text="The slug for this event, created automatically",
    )

    track = models.ForeignKey(
        "program.EventTrack",
        related_name="events",
        help_text="The track this event belongs to",
        on_delete=models.PROTECT,
    )

    video_recording = models.BooleanField(
        default=True,
        help_text="Do we intend to record video of this event?",
    )

    video_streaming = models.BooleanField(
        default=True,
        help_text="Do we intend to stream video of this event?",
    )

    proposal = models.OneToOneField(
        "program.EventProposal",
        null=True,
        blank=True,
        help_text="The event proposal object this event was created from",
        on_delete=models.PROTECT,
        editable=False,
    )

    duration_minutes = models.PositiveIntegerField(
        default=None,
        blank=True,
        help_text="The duration of this event in minutes. Leave blank to use the default from the event_type.",
    )

    demand = models.PositiveIntegerField(
        default=0,
        help_text="The estimated demand for this event. Used by the autoscheduler to pick the optimal location for events. Set to 0 to disable demand constraints for this event.",
    )

    tags = TaggableManager(blank=True)

    class Meta:
        ordering = ["title"]
        unique_together = (("track", "slug"), ("track", "title"))

    def __str__(self):
        return self.title

    def save(self, **kwargs):
        """Create a slug and get duration"""
        if not self.slug:
            self.slug = unique_slugify(
                self.title,
                slugs_in_use=self.__class__.objects.filter(
                    track__camp=self.track.camp,
                ).values_list("slug", flat=True),
            )
        if not self.duration_minutes:
            # we default to the duration of the event_type
            self.duration_minutes = self.event_type.event_duration_minutes
        super().save(**kwargs)

    @property
    def camp(self):
        return self.track.camp

    camp_filter = "track__camp"

    @property
    def speakers_list(self):
        if self.speakers.exists():
            return ", ".join(self.speakers.all().values_list("name", flat=True))
        return False

    def get_absolute_url(self):
        return reverse(
            "program:event_detail",
            kwargs={"camp_slug": self.camp.slug, "event_slug": self.slug},
        )

    def serialize(self):
        data = {
            "title": self.title,
            "slug": self.slug,
            "abstract": self.abstract,
            "speaker_slugs": [speaker.slug for speaker in self.speakers.all()],
            "event_type": self.event_type.name,
        }

        if self.video_recording and self.video_streaming:
            video_state = "to-be-streamed-to-be-recorded"
        elif self.video_recording:
            video_state = "to-be-recorded-not-to-be-streamed"
        elif self.video_streaming:
            video_state = "to-be-streamed-not-to-be-recorded"
        else:
            video_state = "not-to-be-recorded-not-to-be-streamed"

        data["video_state"] = video_state

        return data

    @property
    def duration(self):
        return timedelta(minutes=self.duration_minutes)


class EventInstance(ExportModelOperationsMixin("event_instance"), CampRelatedModel):
    """The old way of scheduling events. Model to be deleted after prod data migration"""

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="This field is mostly here to keep Frab happy, it is not the PK of the model",
    )

    event = models.ForeignKey(
        "program.event",
        related_name="instances",
        on_delete=models.PROTECT,
    )

    when = DateTimeRangeField(null=True, blank=True)

    notifications_sent = models.BooleanField(default=False)

    location = models.ForeignKey(
        "program.EventLocation",
        related_name="eventinstances",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    autoscheduled = models.BooleanField(
        default=False,
        help_text="True if this was created by the autoscheduler.",
    )

    class Meta:
        ordering = ["when"]
        # we do not want overlapping instances in the same location
        constraints = [
            ExclusionConstraint(
                name="prevent_eventinstance_location_overlaps",
                expressions=[
                    ("when", RangeOperators.OVERLAPS),
                    ("location", RangeOperators.EQUAL),
                ],
            ),
        ]

    def __str__(self):
        return f"{self.event} ({self.when})"

    def clean_speakers(self):
        """Check if all speakers are available"""
        for speaker in self.event.speakers.all():
            if not speaker.is_available(
                when=self.event_slot.when,
                ignore_eventinstances=[self.pk],
            ):
                raise ValidationError(
                    f"The speaker {speaker} is not available at this time",
                )

    def save(self, *args, clean_speakers=True, **kwargs):
        """Validate speakers (unless we are asked not to)"""
        if "commit" not in kwargs or kwargs["commit"]:
            # we are saving for real
            if clean_speakers:
                self.clean_speakers()
        super().save(*args, **kwargs)

    @property
    def camp(self):
        return self.event.camp

    camp_filter = "event__track__camp"

    @property
    def schedule_date(self):
        """Returns the schedule date of this eventinstance. Schedule date is determined by substracting
        settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS from the eventinstance start time. This means that if
        an event is scheduled for 00:30 wednesday evening (technically thursday) then the date
        after substracting 5 hours would be wednesdays date, not thursdays
        (given settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS=5)
        """
        return (self.when.lower - timedelta(hours=settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS)).date()

    @property
    def timeslots(self):
        """Find the number of timeslots this eventinstance takes up"""
        seconds = (self.when.upper - self.when.lower).seconds
        minutes = seconds / 60
        return minutes / settings.SCHEDULE_TIMESLOT_LENGTH_MINUTES

    def get_ics_event(self):
        ievent = icalendar.Event()
        ievent["summary"] = self.event.title
        ievent["description"] = self.event.abstract
        ievent["dtstart"] = icalendar.vDatetime(self.when.lower).to_ical()
        ievent["dtend"] = icalendar.vDatetime(self.when.upper).to_ical()
        ievent["location"] = icalendar.vText(self.location.name)
        return ievent

    def serialize(self, user=None):
        data = {
            "title": self.event.title,
            "slug": self.event.slug + "-" + str(self.id),
            "event_slug": self.event.slug,
            "from": self.when.lower.isoformat(),
            "to": self.when.upper.isoformat(),
            "url": str(self.event.get_absolute_url()),
            "id": self.id,
            "bg-color": self.event.event_type.color,
            "fg-color": "#fff" if self.event.event_type.light_text else "#000",
            "event_type": self.event.event_type.slug,
            "event_track": self.event.track.slug,
            "location": self.location.slug,
            "location_icon": self.location.icon,
            "timeslots": self.timeslots,
        }

        if self.event.video_recording and self.event.video_streaming:
            video_state = "to-be-recorded-to-be-streamed"
        elif self.event.video_recording:
            video_state = "to-be-recorded-not-to-be-streamed"
        elif self.event.video_streaming:
            video_state = "to-be-streamed-not-to-be-recorded"
        else:
            video_state = "not-to-be-recorded-not-to-be-streamed"

        data["video_state"] = video_state

        if user and user.is_authenticated:
            is_favorited = user.favorites.filter(event_instance=self).exists()
            data["is_favorited"] = is_favorited

        return data

    @property
    def duration(self):
        """Return a timedelta of the lenght of this EventInstance"""
        return self.when.upper - self.when.lower

    @property
    def overflow(self):
        if self.event.demand > self.location.capacity:
            return (self.location.capacity - self.event.demand) * -1
        return 0


class Speaker(ExportModelOperationsMixin("speaker"), CampRelatedModel):
    """A Person (co)anchoring one or more events on a camp."""

    name = models.CharField(max_length=150, help_text="Name or alias of the speaker")

    email = models.EmailField(max_length=150, help_text="The email of the speaker.")

    biography = models.TextField(help_text="Markdown is supported.")

    slug = models.SlugField(
        blank=True,
        max_length=255,
        help_text="The slug for this speaker, will be autocreated",
    )

    camp = models.ForeignKey(
        "camps.Camp",
        null=True,
        related_name="speakers",
        help_text="The camp this speaker belongs to",
        on_delete=models.PROTECT,
    )

    events = models.ManyToManyField(
        Event,
        blank=True,
        help_text="The event(s) this speaker is anchoring",
        related_name="speakers",
    )

    proposal = models.OneToOneField(
        "program.SpeakerProposal",
        null=True,
        blank=True,
        help_text="The speaker proposal object this speaker was created from",
        on_delete=models.PROTECT,
        editable=False,
    )

    needs_oneday_ticket = models.BooleanField(
        default=False,
        help_text="Check if BornHack needs to provide a free one-day ticket for this speaker",
    )

    event_conflicts = models.ManyToManyField(
        "program.Event",
        related_name="speaker_conflicts",
        blank=True,
        help_text="The Events this person wishes to attend. The AutoScheduler will avoid conflicts.",
    )

    class Meta:
        ordering = ["name"]
        unique_together = ("camp", "slug")

    def __str__(self):
        return f"{self.name} ({self.camp})"

    def save(self, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.filter(camp=self.camp).values_list(
                    "slug",
                    flat=True,
                ),
            )
        super().save(**kwargs)

    def get_absolute_url(self):
        return reverse_lazy(
            "program:speaker_detail",
            kwargs={"camp_slug": self.camp.slug, "slug": self.slug},
        )

    def serialize(self):
        data = {"name": self.name, "slug": self.slug, "biography": self.biography}
        return data

    def is_available(self, when, ignore_event_slot_ids=None):
        """A speaker is available if the person has positive availability for the period and
        if the speaker is not in another event at the time, or if the person has not submitted
        any availability at all
        """
        ignore_event_slot_ids = ignore_event_slot_ids or []
        if not self.availabilities.exists():
            # we have no availability at all for this speaker, assume they are available
            return True

        if not self.availabilities.filter(when__contains=when, available=True).exists():
            # we have no positive availability for this speaker
            return False

        # get all slots for this speaker which overlap with the period
        slots = self.camp.event_slots.filter(event__speakers=self, when__overlap=when)

        # do we have any slots we want to ignore?
        if ignore_event_slot_ids:
            slots = slots.exclude(pk__in=ignore_event_slot_ids)

        if slots.exists():
            # speaker is in another event at this time
            return False

        # speaker is available
        return True

    def scheduled_event_slots(self):
        """Returns a QuerySet of all EventSlots scheduled for this speaker"""
        return self.camp.event_slots.filter(event__speakers=self)

    @property
    def title(self):
        """Convenience method to return the proper host_title"""
        if self.events.values_list("event_type").distinct().count() > 1:
            # we have different eventtypes, use generic title
            return "Person"
        return self.events.first().event_type.host_title


class Favorite(ExportModelOperationsMixin("favorite"), models.Model):
    user = models.ForeignKey(
        "auth.User",
        related_name="favorites",
        on_delete=models.PROTECT,
    )
    event_instance = models.ForeignKey(
        "program.EventInstance",
        on_delete=models.PROTECT,
    )

    class Meta:
        unique_together = ["user", "event_instance"]


###############################################################################


class EventFeedback(
    ExportModelOperationsMixin("event_feedback"),
    CampRelatedModel,
    UUIDModel,
):
    """This model contains all feedback for Events
    Each user can submit exactly one feedback per Event
    """

    class Meta:
        unique_together = [("user", "event")]

    YESNO_CHOICES = [(True, "Yes"), (False, "No")]

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        help_text="The User who wrote this feedback",
    )

    event = models.ForeignKey(
        "program.event",
        related_name="feedbacks",
        on_delete=models.PROTECT,
        help_text="The Event this feedback is about",
    )

    expectations_fulfilled = models.BooleanField(
        choices=YESNO_CHOICES,
        help_text="Did the event live up to your expectations?",
    )

    attend_speaker_again = models.BooleanField(
        choices=YESNO_CHOICES,
        help_text="Would you attend another event with the same speaker?",
    )

    RATING_CHOICES = [(n, f"{n}") for n in range(6)]

    rating = models.IntegerField(
        choices=RATING_CHOICES,
        help_text="Rating/Score (5 is best)",
    )

    comment = models.TextField(blank=True, help_text="Any other comments or feedback?")

    approved = models.BooleanField(
        blank=True,
        null=True,
        help_text="Approve feedback? It will not be visible to the Event owner before it is approved.",
    )

    @property
    def camp(self):
        return self.event.camp

    camp_filter = "event__track__camp"

    def get_absolute_url(self):
        return reverse(
            "program:event_feedback_detail",
            kwargs={"camp_slug": self.camp.slug, "event_slug": self.event.slug},
        )


# classes and functions below here was used by picture handling for speakers before it was removed in May 2018 by tyk


class CustomUrlStorage(FileSystemStorage):
    """Must exist because it is mentioned in old migrations.
    Can be removed when we clean up old migrations at some point
    """


def get_speaker_picture_upload_path():
    """Must exist because it is mentioned in old migrations.
    Can be removed when we clean up old migrations at some point
    """


def get_speakerproposal_picture_upload_path():
    """Must exist because it is mentioned in old migrations.
    Can be removed when we clean up old migrations at some point
    """


def get_speakersubmission_picture_upload_path():
    """Must exist because it is mentioned in old migrations.
    Can be removed when we clean up old migrations at some point
    """
