from __future__ import unicode_literals
from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from utils.models import CreatedUpdatedModel
from django.core.exceptions import ValidationError
from datetime import timedelta


class EventType(CreatedUpdatedModel):
    """ Every event needs to have a type. """
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    color = models.CharField(max_length=50)
    light_text = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class Event(CreatedUpdatedModel):
    """ Something that is on the program one or more times. """
    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True, max_length=255)
    abstract = models.TextField()
    event_type = models.ForeignKey(EventType)
    camp = models.ForeignKey('camps.Camp', null=True, related_name="events")

    class Meta:
        ordering = ['title']

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.camp.title)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Event, self).save(**kwargs)


class EventInstance(CreatedUpdatedModel):
    """ An instance of an event """
    event = models.ForeignKey('program.event', related_name='instances')
    when = DateTimeRangeField()

    class Meta:
        ordering = ['when']

    def __unicode__(self):
        return '%s (%s)' % (self.event, self.when)

    def __clean__(self):
        errors = []
        if self.when.lower > self.when.upper:
            errors.append(ValidationError({'when', "Start should be earlier than finish"}))

        if self.when.lower.time().minute != 0 and self.when.lower.time().minute != 30:
            errors.append(ValidationError({'when', "Start time minute should be 0 or 30."}))

        if self.when.upper.time().minute != 0 and self.when.upper.time().minute != 30:
            errors.append(ValidationError({'when', "End time minute should be 0 or 30."}))

        if errors:
           raise ValidationError(errors)

    @property
    def schedule_date(self):
        """
            Returns the schedule date of this eventinstance. Schedule date is determined by substracting
            settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS from the eventinstance start time. This means that if
            an event is scheduled for 00:30 wednesday evening (technically thursday) then the date
            after substracting 5 hours would be wednesdays date, not thursdays.
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


class Speaker(CreatedUpdatedModel):
    """ A Person anchoring an event. """
    name = models.CharField(max_length=150)
    biography = models.TextField()
    picture = models.ImageField(null=True, blank=True)
    slug = models.SlugField(blank=True, max_length=255)
    camp = models.ForeignKey('camps.Camp', null=True, related_name="speakers")
    events = models.ManyToManyField(
        Event,
        related_name='speakers',
        related_query_name='speaker',
        blank=True,
    )

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.camp)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Speaker, self).save(**kwargs)

