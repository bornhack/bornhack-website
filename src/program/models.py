import logging
import uuid
from datetime import timedelta

import icalendar
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.postgres.fields import DateTimeRangeField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify
from utils.models import CampRelatedModel, CreatedUpdatedModel, UUIDModel

from .email import (
    add_eventproposal_accepted_email,
    add_eventproposal_rejected_email,
    add_speakerproposal_accepted_email,
    add_speakerproposal_rejected_email,
)

logger = logging.getLogger("bornhack.%s" % __name__)


class UrlType(CreatedUpdatedModel):
    """
    Each Url object has a type.
    """

    name = models.CharField(
        max_length=25, help_text="The name of this type", unique=True
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


class Url(CampRelatedModel):
    """
        This model contains URLs related to
        - SpeakerProposals
        - EventProposals
        - Speakers
        - Events
        Each URL has a UrlType and a GenericForeignKey to the model to which it belongs.
        When a SpeakerProposal or EventProposal is approved the related URLs will be copied with FK to the new Speaker/Event objects.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    url = models.URLField(help_text="The actual URL")

    urltype = models.ForeignKey(
        "program.UrlType", help_text="The type of this URL", on_delete=models.PROTECT
    )

    speakerproposal = models.ForeignKey(
        "program.SpeakerProposal",
        null=True,
        blank=True,
        help_text="The speaker proposal object this URL belongs to",
        on_delete=models.PROTECT,
        related_name="urls",
    )

    eventproposal = models.ForeignKey(
        "program.EventProposal",
        null=True,
        blank=True,
        help_text="The event proposal object this URL belongs to",
        on_delete=models.PROTECT,
        related_name="urls",
    )

    speaker = models.ForeignKey(
        "program.Speaker",
        null=True,
        blank=True,
        help_text="The speaker proposal object this URL belongs to",
        on_delete=models.PROTECT,
        related_name="urls",
    )

    event = models.ForeignKey(
        "program.Event",
        null=True,
        blank=True,
        help_text="The event proposal object this URL belongs to",
        on_delete=models.PROTECT,
        related_name="urls",
    )

    def __str__(self):
        return self.url

    def clean(self):
        """ Make sure we have exactly one FK """
        fks = 0
        if self.speakerproposal:
            fks += 1
        if self.eventproposal:
            fks += 1
        if self.speaker:
            fks += 1
        if self.event:
            fks += 1
        if fks > 1:
            raise (
                ValidationError(
                    "Url objects must have maximum one FK, this has %s" % fks
                )
            )

    @property
    def owner(self):
        """
        Return the object this Url belongs to
        """
        if self.speakerproposal:
            return self.speakerproposal
        elif self.eventproposal:
            return self.eventproposal
        elif self.speaker:
            return self.speaker
        elif self.event:
            return self.event
        else:
            return None

    @property
    def camp(self):
        return self.owner.camp

    camp_filter = [
        "speakerproposal__camp",
        "eventproposal__track__camp",
        "speaker__camp",
        "event__track__camp",
    ]


###############################################################################


class UserSubmittedModel(CampRelatedModel):
    """
        An abstract model containing the stuff that is shared
        between the SpeakerProposal and EventProposal models.
    """

    class Meta:
        abstract = True

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)

    PROPOSAL_PENDING = "pending"
    PROPOSAL_APPROVED = "approved"
    PROPOSAL_REJECTED = "rejected"

    ROPOSAL_STATUSES = [PROPOSAL_PENDING, PROPOSAL_APPROVED, PROPOSAL_REJECTED]

    PROPOSAL_STATUS_CHOICES = [
        (PROPOSAL_PENDING, "Pending approval"),
        (PROPOSAL_APPROVED, "Approved"),
        (PROPOSAL_REJECTED, "Rejected"),
    ]

    proposal_status = models.CharField(
        max_length=50, choices=PROPOSAL_STATUS_CHOICES, default=PROPOSAL_PENDING
    )

    reason = models.TextField(
        blank=True, help_text="The reason this proposal was accepted or rejected.",
    )

    def __str__(self):
        return "%s (submitted by: %s, status: %s)" % (
            self.headline,
            self.user,
            self.proposal_status,
        )

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


class SpeakerProposal(UserSubmittedModel):
    """ A speaker proposal """

    camp = models.ForeignKey(
        "camps.Camp",
        related_name="speakerproposals",
        on_delete=models.PROTECT,
        editable=False,
    )

    name = models.CharField(
        max_length=150, help_text="Name or alias of the speaker/artist/host"
    )

    email = models.EmailField(
        blank=True,
        max_length=150,
        help_text="The email of the speaker/artist/host. Defaults to the logged in users email if empty.",
    )

    biography = models.TextField(
        help_text="Biography of the speaker/artist/host. Markdown is supported."
    )

    submission_notes = models.TextField(
        help_text="Private notes for this speaker/artist/host. Only visible to the submitting user and the BornHack organisers.",
        blank=True,
    )

    needs_oneday_ticket = models.BooleanField(
        default=False,
        help_text="Check if BornHack needs to provide a free one-day ticket for this speaker",
    )

    @property
    def headline(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy(
            "program:speakerproposal_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.uuid},
        )

    def mark_as_approved(self, request):
        """ Marks a SpeakerProposal as approved, including creating/updating the related Speaker object """
        speakerproposalmodel = apps.get_model("program", "speakerproposal")
        # create a Speaker if we don't have one
        if not hasattr(self, "speaker"):
            speakermodel = apps.get_model("program", "speaker")
            speaker = speakermodel()
            speaker.proposal = self
        else:
            speaker = self.speaker

        # set Speaker data
        speaker.camp = self.camp
        if self.email:
            email = self.email
        else:
            email = request.user.email
        speaker.email = email
        speaker.name = self.name
        speaker.biography = self.biography
        speaker.needs_oneday_ticket = self.needs_oneday_ticket
        speaker.save()

        # mark as approved and save
        self.proposal_status = speakerproposalmodel.PROPOSAL_APPROVED
        self.save()

        # copy all the URLs to the speaker object
        speaker.urls.clear()
        for url in self.urls.all():
            Url.objects.create(url=url.url, urltype=url.urltype, speaker=speaker)

        # a message to the admin
        messages.success(
            request, "Speaker object %s has been created/updated" % speaker
        )
        add_speakerproposal_accepted_email(self)

    def mark_as_rejected(self, request):
        speakerproposalmodel = apps.get_model("program", "speakerproposal")
        self.proposal_status = speakerproposalmodel.PROPOSAL_REJECTED
        self.save()
        messages.success(request, "SpeakerProposal %s has been rejected" % self.name)
        add_speakerproposal_rejected_email(self)


class EventProposal(UserSubmittedModel):
    """ An event proposal """

    track = models.ForeignKey(
        "program.EventTrack",
        related_name="eventproposals",
        help_text="The track this event belongs to",
        on_delete=models.PROTECT,
    )

    title = models.CharField(
        max_length=255,
        help_text="The title of this event. Keep it short and memorable.",
    )

    abstract = models.TextField(
        help_text="The abstract for this event. Describe what the audience can expect to see/hear.",
        blank=True,
    )

    event_type = models.ForeignKey(
        "program.EventType", help_text="The type of event", on_delete=models.PROTECT
    )

    speakers = models.ManyToManyField(
        "program.SpeakerProposal",
        blank=True,
        help_text="Pick the speaker(s) for this event. If you cannot see anything here you need to go back and create Speaker Proposal(s) first.",
        related_name="eventproposals",
    )

    allow_video_recording = models.BooleanField(
        default=False,
        help_text="Recordings are made available under the <b>CC BY-SA 4.0</b> license. Uncheck if you do not want the event recorded, or if you cannot accept the license.",
    )

    duration = models.IntegerField(
        default=None,
        null=True,
        blank=True,
        help_text="How much time (in minutes) should we set aside for this act? Please keep it between 60 and 180 minutes (1-3 hours).",
    )

    submission_notes = models.TextField(
        help_text="Private notes for this event. Only visible to the submitting user and the BornHack organisers.",
        blank=True,
    )

    use_provided_speaker_laptop = models.BooleanField(
        help_text="Will you be using the provided speaker laptop?", default=True
    )

    @property
    def camp(self):
        return self.track.camp

    camp_filter = "track__camp"

    @property
    def headline(self):
        return self.title

    def get_absolute_url(self):
        return reverse_lazy(
            "program:eventproposal_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.uuid},
        )

    def get_available_speakerproposals(self):
        """
        Return all SpeakerProposals submitted by the user who submitted this EventProposal,
        which are not already added to this EventProposal
        """
        return SpeakerProposal.objects.filter(
            camp=self.track.camp, user=self.user
        ).exclude(uuid__in=self.speakers.all().values_list("uuid"))

    def mark_as_approved(self, request):
        eventmodel = apps.get_model("program", "event")
        eventproposalmodel = apps.get_model("program", "eventproposal")
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
        event.save()
        # loop through the speakerproposals linked to this eventproposal and associate any related speaker objects with this event
        for sp in self.speakers.all():
            try:
                event.speakers.add(sp.speaker)
            except ObjectDoesNotExist:
                # clean up
                event.urls.clear()
                event.delete()
                raise ValidationError("Not all speakers are approved or created yet.")

        self.proposal_status = eventproposalmodel.PROPOSAL_APPROVED
        self.save()

        # clear any old urls from the event object and copy all the URLs from the proposal
        event.urls.clear()
        for url in self.urls.all():
            Url.objects.create(url=url.url, urltype=url.urltype, event=event)

        messages.success(request, "Event object %s has been created/updated" % event)
        add_eventproposal_accepted_email(self)

    def mark_as_rejected(self, request):
        eventproposalmodel = apps.get_model("program", "eventproposal")
        self.proposal_status = eventproposalmodel.PROPOSAL_REJECTED
        self.save()
        messages.success(request, "EventProposal %s has been rejected" % self.title)
        add_eventproposal_rejected_email(self)


###############################################################################


class EventTrack(CampRelatedModel):
    """ All events belong to a track. Administration of a track can be delegated to one or more users. """

    name = models.CharField(max_length=100, help_text="The name of this Track")

    slug = models.SlugField(help_text="The url slug for this Track")

    camp = models.ForeignKey(
        "camps.Camp",
        related_name="eventtracks",
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
        return self.name

    class Meta:
        unique_together = (("camp", "slug"), ("camp", "name"))

    def serialize(self):
        return {"name": self.name, "slug": self.slug}


class EventLocation(CampRelatedModel):
    """ The places where stuff happens """

    name = models.CharField(max_length=100)

    slug = models.SlugField()

    icon = models.CharField(
        max_length=100,
        help_text="Name of the fontawesome icon to use without the 'fa-' part",
    )

    camp = models.ForeignKey(
        "camps.Camp", related_name="eventlocations", on_delete=models.PROTECT
    )

    def __str__(self):
        return "{} ({})".format(self.name, self.camp)

    class Meta:
        unique_together = (("camp", "slug"), ("camp", "name"))

    def serialize(self):
        return {"name": self.name, "slug": self.slug, "icon": self.icon}


class EventType(CreatedUpdatedModel):
    """ Every event needs to have a type. """

    name = models.CharField(
        max_length=100, unique=True, help_text="The name of this event type"
    )

    slug = models.SlugField()

    description = models.TextField(
        default="",
        help_text="The description of this type of event. Used in content submission flow.",
        blank=True,
    )

    color = models.CharField(
        max_length=50, help_text="The background color of this event type"
    )

    light_text = models.BooleanField(
        default=False, help_text="Check if this event type should use white text color"
    )

    icon = models.CharField(
        max_length=25,
        help_text="Name of the fontawesome icon to use, without the 'fa-' part",
        default="wrench",
    )

    notifications = models.BooleanField(
        default=False, help_text="Check to send notifications for this event type"
    )

    public = models.BooleanField(
        default=False, help_text="Check to permit users to submit events of this type"
    )

    include_in_event_list = models.BooleanField(
        default=True, help_text="Include events of this type in the event list?"
    )

    host_title = models.CharField(
        max_length=30,
        help_text='What to call someone hosting this type of event. Like "Artist" for Music or "Speaker" for talks.',
        default="Person",
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


class Event(CampRelatedModel):
    """ Something that is on the program one or more times. """

    title = models.CharField(max_length=255, help_text="The title of this event")

    abstract = models.TextField(help_text="The abstract for this event")

    event_type = models.ForeignKey(
        "program.EventType",
        help_text="The type of this event",
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

    video_url = models.URLField(
        max_length=1000, null=True, blank=True, help_text="URL to the recording"
    )

    video_recording = models.BooleanField(
        default=True, help_text="Do we intend to record video of this event?"
    )

    proposal = models.OneToOneField(
        "program.EventProposal",
        null=True,
        blank=True,
        help_text="The event proposal object this event was created from",
        on_delete=models.PROTECT,
        editable=False,
    )

    class Meta:
        ordering = ["title"]
        unique_together = (("track", "slug"), ("track", "title"))

    def __str__(self):
        return "%s (%s)" % (self.title, self.camp.title)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Event, self).save(**kwargs)

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

        if self.video_url:
            video_state = "has-recording"
            data["video_url"] = self.video_url
        elif self.video_recording:
            video_state = "to-be-recorded"
        elif not self.video_recording:
            video_state = "not-to-be-recorded"

        data["video_state"] = video_state

        return data


class EventInstance(CampRelatedModel):
    """ An instance of an event """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="This field is mostly here to keep Frab happy, it is not the PK of the model",
    )

    event = models.ForeignKey(
        "program.event", related_name="instances", on_delete=models.PROTECT
    )

    when = DateTimeRangeField()

    notifications_sent = models.BooleanField(default=False)

    location = models.ForeignKey(
        "program.EventLocation", related_name="eventinstances", on_delete=models.PROTECT
    )

    class Meta:
        ordering = ["when"]

    def __str__(self):
        return "%s (%s)" % (self.event, self.when)

    def clean(self):
        if self.location.camp != self.event.camp:
            raise ValidationError(
                {"location": "Error: This location belongs to a different camp"}
            )

    @property
    def camp(self):
        return self.event.camp

    camp_filter = "event__track__camp"

    @property
    def schedule_date(self):
        """
            Returns the schedule date of this eventinstance. Schedule date is determined by substracting
            settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS from the eventinstance start time. This means that if
            an event is scheduled for 00:30 wednesday evening (technically thursday) then the date
            after substracting 5 hours would be wednesdays date, not thursdays
            (given settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS=5)
        """
        return (
            self.when.lower - timedelta(hours=settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS)
        ).date()

    @property
    def timeslots(self):
        """ Find the number of timeslots this eventinstance takes up """
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

        if self.event.video_url:
            video_state = "has-recording"
            data["video_url"] = self.event.video_url
        elif self.event.video_recording:
            video_state = "to-be-recorded"
        elif not self.event.video_recording:
            video_state = "not-to-be-recorded"

        data["video_state"] = video_state

        if user and user.is_authenticated:
            is_favorited = user.favorites.filter(event_instance=self).exists()
            data["is_favorited"] = is_favorited

        return data


class Speaker(CampRelatedModel):
    """ A Person (co)anchoring one or more events on a camp. """

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

    class Meta:
        ordering = ["name"]
        unique_together = (("camp", "name"), ("camp", "slug"))

    def __str__(self):
        return "%s (%s)" % (self.name, self.camp)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Speaker, self).save(**kwargs)

    def get_absolute_url(self):
        return reverse_lazy(
            "program:speaker_detail",
            kwargs={"camp_slug": self.camp.slug, "slug": self.slug},
        )

    def serialize(self):
        data = {"name": self.name, "slug": self.slug, "biography": self.biography}
        return data


class Favorite(models.Model):
    user = models.ForeignKey(
        "auth.User", related_name="favorites", on_delete=models.PROTECT
    )
    event_instance = models.ForeignKey(
        "program.EventInstance", on_delete=models.PROTECT
    )

    class Meta:
        unique_together = ["user", "event_instance"]


###############################################################################


class EventFeedback(CampRelatedModel, UUIDModel):
    """
    This model contains all feedback for Events
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
        choices=YESNO_CHOICES, help_text="Did the event live up to your expectations?",
    )

    attend_speaker_again = models.BooleanField(
        choices=YESNO_CHOICES,
        help_text="Would you attend another event with the same speaker?",
    )

    RATING_CHOICES = [(n, f"{n}") for n in range(0, 6)]

    rating = models.IntegerField(
        choices=RATING_CHOICES, help_text="Rating/Score (5 is best)",
    )

    comment = models.TextField(blank=True, help_text="Any other comments or feedback?")

    approved = models.NullBooleanField(
        help_text="Approve feedback? It will not be visible to the Event owner before it is approved."
    )

    @property
    def camp(self):
        return self.event.camp

    camp_filter = "event__track__camp"

    def get_absolute_url(self):
        return reverse(
            "program:eventfeedback_detail",
            kwargs={"camp_slug": self.camp.slug, "event_slug": self.event.slug},
        )


# classes and functions below here was used by picture handling for speakers before it was removed in May 2018 by tyk


class CustomUrlStorage(FileSystemStorage):
    """
    Must exist because it is mentioned in old migrations.
    Can be removed when we clean up old migrations at some point
    """

    pass


def get_speaker_picture_upload_path():
    """
    Must exist because it is mentioned in old migrations.
    Can be removed when we clean up old migrations at some point
    """
    pass


def get_speakerproposal_picture_upload_path():
    """
    Must exist because it is mentioned in old migrations.
    Can be removed when we clean up old migrations at some point
    """
    pass


def get_speakersubmission_picture_upload_path():
    """
    Must exist because it is mentioned in old migrations.
    Can be removed when we clean up old migrations at some point
    """
    pass
