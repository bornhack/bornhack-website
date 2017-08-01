import uuid
import os
import icalendar
import CommonMark
import logging

from datetime import timedelta

from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib import messages
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.apps import apps
from django.core.files.base import ContentFile
from django.db.models.signals import post_save

from utils.models import CreatedUpdatedModel, CampRelatedModel
from .email import add_new_speakerproposal_email, add_new_eventproposal_email
from ircbot.models import OutgoingIrcMessage
logger = logging.getLogger("bornhack.%s" % __name__)


class CustomUrlStorage(FileSystemStorage):
    def __init__(self, location=None):
        super(CustomUrlStorage, self).__init__(location)

    def url(self, name):
        url = super(CustomUrlStorage, self).url(name)
        parts = url.split("/")
        if parts[0] != "public":
            # first bit should always be "public"
            return False

        if parts[1] == "speakerproposals":
            # find speakerproposal
            speakerproposal_model = apps.get_model('program', 'speakerproposal')
            try:
                speakerproposal = speakerproposal_model.objects.get(picture_small=name)
                picture = "small"
            except speakerproposal_model.DoesNotExist:
                try:
                    speakerproposal = speakerproposal_model.objects.get(picture_large=name)
                    picture = "large"
                except speakerproposal_model.DoesNotExist:
                    return False
            url = reverse('speakerproposal_picture', kwargs={
                'camp_slug': speakerproposal.camp.slug,
                'pk': speakerproposal.pk,
                'picture': picture,
            })
        else:
            return False

        return url


storage = CustomUrlStorage()


class UserSubmittedModel(CampRelatedModel):
    """
        An abstract model containing the stuff that is shared
        between the SpeakerProposal and EventProposal models.
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

    PROPOSAL_DRAFT = 'draft'
    PROPOSAL_PENDING = 'pending'
    PROPOSAL_APPROVED = 'approved'
    PROPOSAL_REJECTED = 'rejected'
    PROPOSAL_MODIFIED_AFTER_APPROVAL = 'modified after approval'

    PROPOSAL_STATUSES = [
        PROPOSAL_DRAFT,
        PROPOSAL_PENDING,
        PROPOSAL_APPROVED,
        PROPOSAL_REJECTED,
        PROPOSAL_MODIFIED_AFTER_APPROVAL
    ]

    PROPOSAL_STATUS_CHOICES = [
        (PROPOSAL_DRAFT, 'Draft'),
        (PROPOSAL_PENDING, 'Pending approval'),
        (PROPOSAL_APPROVED, 'Approved'),
        (PROPOSAL_REJECTED, 'Rejected'),
        (PROPOSAL_MODIFIED_AFTER_APPROVAL, 'Modified after approval'),
    ]

    proposal_status = models.CharField(
        max_length=50,
        choices=PROPOSAL_STATUS_CHOICES,
        default=PROPOSAL_DRAFT,
    )

    def __str__(self):
        return '%s (submitted by: %s, status: %s)' % (self.headline, self.user, self.proposal_status)

    def save(self, **kwargs):
        if not self.camp.call_for_speakers_open:
            message = 'Call for speakers is not open'
            if hasattr(self, 'request'):
                messages.error(self.request, message)
            raise ValidationError(message)
        super().save(**kwargs)

    def delete(self, **kwargs):
        if not self.camp.call_for_speakers_open:
            message = 'Call for speakers is not open'
            if hasattr(self, 'request'):
                messages.error(self.request, message)
            raise ValidationError(message)
        super().delete(**kwargs)


def get_speakerproposal_picture_upload_path(instance, filename):
    """ We want speakerproposal pictures saved as MEDIA_ROOT/public/speakerproposals/camp-slug/proposal-uuid/filename """
    return 'public/speakerproposals/%(campslug)s/%(proposaluuid)s/%(filename)s' % {
        'campslug': instance.camp.slug,
        'proposaluuid': instance.uuid,
        'filename': filename
    }


def get_speakersubmission_picture_upload_path(instance, filename):
    """ We want speakerproposal pictures saved as MEDIA_ROOT/public/speakerproposals/camp-slug/proposal-uuid/filename """
    return 'public/speakerproposals/%(campslug)s/%(proposaluuid)s/%(filename)s' % {
        'campslug': instance.camp.slug,
        'proposaluuidd': instance.uuid,
        'filename': filename
    }


class SpeakerProposal(UserSubmittedModel):
    """ A speaker proposal """

    camp = models.ForeignKey(
        'camps.Camp',
        related_name='speakerproposals'
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
        upload_to=get_speakerproposal_picture_upload_path,
        help_text='A picture of the speaker',
        storage=storage,
        max_length=255
    )

    picture_small = models.ImageField(
        null=True,
        blank=True,
        upload_to=get_speakerproposal_picture_upload_path,
        help_text='A thumbnail of the speaker picture',
        storage=storage,
        max_length=255
    )

    submission_notes = models.TextField(
        help_text='Private notes for this speaker. Only visible to the submitting user and the BornHack organisers.',
        blank=True
    )

    @property
    def headline(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy('speakerproposal_detail', kwargs={'camp_slug': self.camp.slug, 'pk': self.uuid})

    def mark_as_approved(self):
        speakermodel = apps.get_model('program', 'speaker')
        speakerproposalmodel = apps.get_model('program', 'speakerproposal')
        speaker = speakermodel()
        speaker.camp = self.camp
        speaker.name = self.name
        speaker.biography = self.biography
        if self.picture_small and self.picture_large:
            temp = ContentFile(self.picture_small.read())
            temp.name = os.path.basename(self.picture_small.name)
            speaker.picture_small = temp
            temp = ContentFile(self.picture_large.read())
            temp.name = os.path.basename(self.picture_large.name)
            speaker.picture_large = temp
        speaker.proposal = self
        speaker.save()

        self.proposal_status = speakerproposalmodel.PROPOSAL_APPROVED
        self.save()


class EventProposal(UserSubmittedModel):
    """ An event proposal """

    camp = models.ForeignKey(
        'camps.Camp',
        related_name='eventproposals'
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
        'program.SpeakerProposal',
        blank=True,
        help_text='Pick the speaker(s) for this event. If you cannot see anything here you need to go back and create Speaker Proposal(s) first.',
    )

    allow_video_recording = models.BooleanField(
        default=False,
        help_text='If we can video record the event or not'
    )

    submission_notes = models.TextField(
        help_text='Private notes for this event. Only visible to the submitting user and the BornHack organisers.',
        blank=True
    )

    @property
    def headline(self):
        return self.title

    def get_absolute_url(self):
        return reverse_lazy(
            'eventproposal_detail',
            kwargs={'camp_slug': self.camp.slug, 'pk': self.uuid}
        )

    def mark_as_approved(self):
        eventmodel = apps.get_model('program', 'event')
        eventproposalmodel = apps.get_model('program', 'eventproposal')
        event = eventmodel()
        event.camp = self.camp
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
                event.delete()
                raise ValidationError('Not all speakers are approved or created yet.')

        self.proposal_status = eventproposalmodel.PROPOSAL_APPROVED
        self.save()


@receiver(post_save, sender=EventProposal)
@receiver(post_save, sender=SpeakerProposal)
def notify_proposals(sender, created, instance, **kwargs):
    target = settings.IRCBOT_CHANNELS['orga'] if 'orga' in settings.IRCBOT_CHANNELS else settings.IRCBOT_CHANNELS['default']

    if created and isinstance(instance, SpeakerProposal):
        if not add_new_speakerproposal_email(instance):
            logger.error(
                'Error adding speaker proposal email to outgoing queue for {}'.format(instance)
            )
        OutgoingIrcMessage.objects.create(
            target=target,
            message="New speaker proposal: {} - https://bornhack.dk/admin/program/speakerproposal/{}/change/".format(
                instance.name,
                instance.uuid
            ),
            timeout=timezone.now()+timedelta(minutes=10)
        )

    if created and isinstance(instance, EventProposal):
        if not add_new_eventproposal_email(instance):
            logger.error(
                'Error adding event proposal email to outgoing queue for {}'.format(instance)
            )
        OutgoingIrcMessage.objects.create(
            target=target,
            message="New event proposal: {} - https://bornhack.dk/admin/program/eventproposal/{}/change/".format(
                instance.title,
                instance.uuid
            ),
            timeout=timezone.now()+timedelta(minutes=10)
        )

###############################################################################


class EventLocation(CampRelatedModel):
    """ The places where stuff happens """

    name = models.CharField(
        max_length=100
    )

    slug = models.SlugField()

    icon = models.CharField(
        max_length=100,
        help_text="hex for the unicode character in the fontawesome icon set to use, like 'f000' for 'fa-glass'"
    )

    camp = models.ForeignKey(
        'camps.Camp',
        related_name='eventlocations'
    )

    def __str__(self):
        return '{} ({})'.format(self.name, self.camp)

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

    include_in_event_list = models.BooleanField(
        default=True,
        help_text='Include events of this type in the event list?',
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

    def clean(self):
        if self.location.camp != self.event.camp:
            raise ValidationError({'location': 'Error: This location belongs to a different camp'})

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

    def get_ics_event(self):
        ievent = icalendar.Event()
        ievent['summary'] = self.event.title
        ievent['dtstart'] = icalendar.vDatetime(self.when.lower).to_ical()
        ievent['dtend'] = icalendar.vDatetime(self.when.upper).to_ical()
        ievent['location'] = icalendar.vText(self.location.name)
        return ievent

    def to_json(self, user=None):
        parser = CommonMark.Parser()
        renderer = CommonMark.HtmlRenderer()
        ast = parser.parse(self.event.abstract)
        abstract = renderer.render(ast)

        data = {
            'title': self.event.title,
            'event_slug': self.event.slug,
            'abstract': abstract,
            'from': self.when.lower.astimezone().isoformat(),
            'to': self.when.upper.astimezone().isoformat(),
            'url': str(self.event.get_absolute_url()),
            'id': self.id,
            'speakers': [
                {'name': speaker.name, 'url': str(speaker.get_absolute_url())}
                for speaker in self.event.speakers.all()
            ],
            'bg-color': self.event.event_type.color,
            'fg-color': '#fff' if self.event.event_type.light_text else '#000',
            'event_type': self.event.event_type.slug,
            'location': self.location.slug,
            'location_icon': self.location.icon,
            'timeslots': self.timeslots,
            'video_recording': self.event.video_recording,
        }

        if self.event.video_url:
            data['video_url'] = self.event.video_url

        if user and user.is_authenticated:
            is_favorited = user.favorites.filter(event_instance=self).exists()
            data['is_favorited'] = is_favorited

        return data


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
        related_name='speakers'
    )

    proposal = models.OneToOneField(
        'program.SpeakerProposal',
        null=True,
        blank=True,
        help_text='The speaker proposal object this speaker was created from',
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


class Favorite(models.Model):
    user = models.ForeignKey('auth.User', related_name='favorites')
    event_instance = models.ForeignKey('program.EventInstance')

    class Meta:
        unique_together = ['user', 'event_instance']

