from __future__ import unicode_literals

from django.db import models
from django.utils.text import slugify

from utils.models import CreatedUpdatedModel


class EventType(CreatedUpdatedModel):
    """ Every event needs to have a type. """
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    color = models.CharField(max_length=50)
    light_text = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Event(CreatedUpdatedModel):
    """ Something that is on the program. """
    title = models.CharField(max_length=255)
    slug = models.SlugField(blank=True, max_length=255)
    abstract = models.TextField()
    event_type = models.ForeignKey(EventType)
    days = models.ManyToManyField('camps.Day')
    start = models.TimeField()
    end = models.TimeField()

    def __str__(self):
        return self.title

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Event, self).save(**kwargs)


class Speaker(CreatedUpdatedModel):
    """ Person anchoring an event. """
    name = models.CharField(max_length=150)
    biography = models.TextField()
    picture = models.ImageField(null=True, blank=True)
    events = models.ManyToManyField(
        Event,
        related_name='speakers',
        related_query_name='speaker',
        blank=True,
    )

    def __str__(self):
        return self.name
