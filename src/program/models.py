from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from utils.models import CreatedUpdatedModel, CampRelatedModel
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.core.urlresolvers import reverse_lazy
import uuid


class UserSubmittedModel(CampRelatedModel):
    """
        An abstract model containing the stuff that is shared
        between the SpeakerSubmission and EventSubmission models.
    """

    class Meta:
        abstract = True

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        'auth.User',
    )

    SUBMISSION_DRAFT = 'draft'
    SUBMISSION_PENDING = 'pending'
    SUBMISSION_APPROVED = 'approved'
    SUBMISSION_REJECTED = 'rejected'

    SUBMISSION_STATUSES = [
        SUBMISSION_DRAFT,
        SUBMISSION_PENDING,
        SUBMISSION_APPROVED,
        SUBMISSION_REJECTED
    ]

    SUBMISSION_STATUS_CHOICES = [
        (SUBMISSION_DRAFT, 'Draft'),
        (SUBMISSION_PENDING, 'Pending approval'),
        (SUBMISSION_APPROVED, 'Approved'),
        (SUBMISSION_REJECTED, 'Rejected'),
    ]

    submission_status = models.CharField(
        max_length=50,
        choices=SUBMISSION_STATUS_CHOICES,
        default=SUBMISSION_DRAFT,
    )

    def __str__(self):
        return '%s (submitted by: %s, status: %s)' % (self.headline, self.user, self.submission_status)


def get_speakersubmission_picture_upload_path(instance, filename):
    """ We want speakersubmission pictures saved as MEDIA_ROOT/public/speakersubmissions/camp-slug/submission-uuid/filename """
    return 'public/speakersubmissions/%(campslug)s/%(submissionuuid)s/%(filename)s' % {
        'campslug': instance.camp.slug,
        'submissionuuidd': instance.uuid,
        'filename': filename
    }


class SpeakerSubmission(UserSubmittedModel):
    """ A speaker submission """

    camp = models.ForeignKey(
        'camps.Camp',
        related_name='speakersubmissions'
    )

    name = models.CharField(
        max_length=150,
        help_text='Name or alias of the speaker',
    )

    biography = models.TextField(
        help_text='Markdown is supported.'
    )

    picture_large = models.ImageField(
        null=True,
        blank=True,
        upload_to=get_speakersubmission_picture_upload_path,
        help_text='A picture of the speaker'
    )

    picture_small = models.ImageField(
        null=True,
        blank=True,
        upload_to=get_speakersubmission_picture_upload_path,
        help_text='A thumbnail of the speaker picture'
    )

    @property
    def headline(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy('speakersubmission_detail', kwargs={'camp_slug': self.camp.slug, 'pk': self.uuid})


class EventSubmission(UserSubmittedModel):
    """ An event submission """

    camp = models.ForeignKey(
        'camps.Camp',
        related_name='eventsubmissions'
    )

    title = models.CharField(
        max_length=255,
        help_text='The title of this event',
    )

    abstract = models.TextField(
        help_text='The abstract for this event'
    )

    event_type = models.ForeignKey(
        'program.EventType',
        help_text='The type of event',
    )

    speakers = models.ManyToManyField(
        'program.SpeakerSubmission',
        blank=True,
        help_text='Pick the speaker(s) for this event',
    )

    @property
    def headline(self):
        return self.title

    def get_absolute_url(self):
        return reverse_lazy('eventsubmission_detail', kwargs={'camp_slug': self.camp.slug, 'pk': self.uuid})


#############################################################################################


class EventLocation(CampRelatedModel):
    """ The places where stuff happens """

    name = models.CharField(
        max_length=100
    )

    slug = models.SlugField()

    icon = models.CharField(
        max_length=100
    )

    camp = models.ForeignKey(
        'camps.Camp',
        related_name='eventlocations'
    )

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (('camp', 'slug'), ('camp', 'name'))


class EventType(CreatedUpdatedModel):
    """ Every event needs to have a type. """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='The name of this event type',
    )

    slug = models.SlugField()

    color = models.CharField(
        max_length=50,
        help_text='The background color of this event type',
    )

    light_text = models.BooleanField(
        default=False,
        help_text='Check if this event type should use white text color',
    )

    notifications = models.BooleanField(
        default=False,
        help_text='Check to send notifications for this event type',
    )

    public = models.BooleanField(
        default=False,
        help_text='Check to permit users to submit events of this type',
    )

    def __str__(self):
        return self.name


class Event(CampRelatedModel):
    """ Something that is on the program one or more times. """

    title = models.CharField(
        max_length=255,
        help_text='The title of this event',
    )

    abstract = models.TextField(
        help_text='The abstract for this event'
    )

    event_type = models.ForeignKey(
        'program.EventType',
        help_text='The type of this event',
    )

    slug = models.SlugField(
        blank=True,
        max_length=255,
        help_text='The slug for this event, created automatically',
    )

    camp = models.ForeignKey(
        'camps.Camp',
        related_name='events',
        help_text='The camp this event belongs to',
    )

    video_url = models.URLField(
        max_length=1000,
        null=True,
        blank=True,
        help_text='URL to the recording'
    )

    video_recording = models.BooleanField(
        default=True,
        help_text='Do we intend to record video of this event?'
    )

    class Meta:
        ordering = ['title']
        unique_together = (('camp', 'slug'), ('camp', 'title'))

    def __str__(self):
        return '%s (%s)' % (self.title, self.camp.title)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Event, self).save(**kwargs)

    @property
    def speakers_list(self):
        if self.speakers.exists():
            return ", ".join(self.speakers.all().values_list('name', flat=True))
        return False

    def get_absolute_url(self):
        return reverse_lazy('event_detail', kwargs={'camp_slug': self.camp.slug, 'slug': self.slug})


class EventInstance(CampRelatedModel):
    """ An instance of an event """

    event = models.ForeignKey(
        'program.event',
        related_name='instances'
    )

    when = DateTimeRangeField()

    notifications_sent = models.BooleanField(
        default=False
    )

    location = models.ForeignKey(
        'program.EventLocation',
        related_name='eventinstances'
    )

    class Meta:
        ordering = ['when']

    def __str__(self):
        return '%s (%s)' % (self.event, self.when)

    def __clean__(self):
        errors = []
        if self.location.camp != self.event.camp:
            errors.append(ValidationError({'location', "Error: This location belongs to a different camp"}))

        if errors:
            raise ValidationError(errors)

    @property
    def camp(self):
        return self.event.camp

    @property
    def schedule_date(self):
        """
            Returns the schedule date of this eventinstance. Schedule date is determined by substracting
            settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS from the eventinstance start time. This means that if
            an event is scheduled for 00:30 wednesday evening (technically thursday) then the date
            after substracting 5 hours would be wednesdays date, not thursdays
            (given settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS=5)
        """
        return (self.when.lower-timedelta(hours=settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS)).date()

    @property
    def timeslots(self):
        """
            Find the number of timeslots this eventinstance takes up
        """
        seconds = (self.when.upper-self.when.lower).seconds
        minutes = seconds / 60
        return minutes / settings.SCHEDULE_TIMESLOT_LENGTH_MINUTES


def get_speaker_picture_upload_path(instance, filename):
    """ We want speaker pictures are saved as MEDIA_ROOT/public/speakers/camp-slug/speaker-slug/filename """
    return 'public/speakers/%(campslug)s/%(speakerslug)s/%(filename)s' % {
        'campslug': instance.camp.slug,
        'speakerslug': instance.slug,
        'filename': filename
    }


class Speaker(CampRelatedModel):
    """ A Person (co)anchoring one or more events on a camp. """

    name = models.CharField(
        max_length=150,
        help_text='Name or alias of the speaker',
    )

    biography = models.TextField(
        help_text='Markdown is supported.'
    )

    picture_small = models.ImageField(
        null=True,
        blank=True,
        upload_to=get_speaker_picture_upload_path,
        help_text='A thumbnail of the speaker picture'
    )

    picture_large = models.ImageField(
        null=True,
        blank=True,
        upload_to=get_speaker_picture_upload_path,
        help_text='A picture of the speaker'
    )

    slug = models.SlugField(
        blank=True,
        max_length=255,
        help_text='The slug for this speaker, will be autocreated',
    )

    camp = models.ForeignKey(
        'camps.Camp',
        null=True,
        related_name='speakers',
        help_text='The camp this speaker belongs to',
    )

    events = models.ManyToManyField(
        Event,
        blank=True,
        help_text='The event(s) this speaker is anchoring',
    )

    submission = models.OneToOneField(
        'program.SpeakerSubmission',
        null=True,
        blank=True,
        help_text='The speaker submission object this speaker was created from',
    )

    class Meta:
        ordering = ['name']
        unique_together = (('camp', 'name'), ('camp', 'slug'))

    def __str__(self):
        return '%s (%s)' % (self.name, self.camp)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Speaker, self).save(**kwargs)

    def get_absolute_url(self):
        return reverse_lazy('speaker_detail', kwargs={'camp_slug': self.camp.slug, 'slug': self.slug})


