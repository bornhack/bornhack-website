from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from utils.models import CreatedUpdatedModel, CampRelatedModel
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.core.urlresolvers import reverse_lazy


class UserSubmittedModel(CampRelatedModel):
    class Meta:
        abstract = True

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

    @property
    def is_public(self):
        if self.submission_status == self.SUBMISSION_APPROVED:
            return True
        else:
            return False


class EventLocation(CampRelatedModel):
    """ The places where stuff happens """
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    icon = models.CharField(max_length=100)
    camp = models.ForeignKey('camps.Camp', null=True, related_name="eventlocations")

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (('camp', 'slug'), ('camp', 'name'))


class EventType(CreatedUpdatedModel):
    """ Every event needs to have a type. """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField()
    color = models.CharField(max_length=50)
    light_text = models.BooleanField(default=False)
    notifications = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Event(UserSubmittedModel):
    """ Something that is on the program one or more times. """
    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True, max_length=255)
    abstract = models.TextField()
    event_type = models.ForeignKey(EventType)
    camp = models.ForeignKey('camps.Camp', null=True, related_name="events")

    video_url = models.URLField(
        max_length=1000,
        null=True,
        blank=True,
        help_text=_('URL to the recording.')
    )
    video_recording = models.BooleanField(
        default=True,
        help_text=_('Whether the event will be video recorded or not.')
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
    event = models.ForeignKey('program.event', related_name='instances')
    when = DateTimeRangeField()
    notifications_sent = models.BooleanField(default=False)
    location = models.ForeignKey('program.EventLocation', related_name='eventinstances')

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


class Speaker(UserSubmittedModel):
    """ A Person anchoring an event. """
    name = models.CharField(max_length=150)
    biography = models.TextField(
        help_text='Markdown is supported.'
    )
    picture_small = models.ImageField(
        null=True,
        blank=True,
        upload_to=get_speaker_picture_upload_path,
        help_text='A thumbnail of your picture'
    )
    picture_large = models.ImageField(
        null=True,
        blank=True,
        upload_to=get_speaker_picture_upload_path,
        help_text='A picture of you'
    )
    slug = models.SlugField(blank=True, max_length=255)
    camp = models.ForeignKey('camps.Camp', null=True, related_name="speakers")
    events = models.ManyToManyField(
        Event,
        blank=True,
    )

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['name']
        unique_together = (('camp', 'name'), ('camp', 'slug'), ('camp', 'user'))

    def __str__(self):
        return '%s (%s)' % (self.name, self.camp)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Speaker, self).save(**kwargs)

    def get_absolute_url(self):
        return reverse_lazy('speaker_detail', kwargs={'camp_slug': self.camp.slug, 'slug': self.slug})

    def clean(self):
        if self.slug == "create":
            # this is a reserved word used in urls.py
            raise ValidationError({'name': 'This name is reserved, please choose another'})

