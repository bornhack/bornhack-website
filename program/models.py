"""Model definitions for the program app."""
from __future__ import unicode_literals

from django.db import models
from utils.models import CreatedUpdatedModel


class EventType(CreatedUpdatedModel):
    '''Every event needs to have a type.'''
    name = models.CharField(max_length=100)
    slug = models.SlugField()


class Event(CreatedUpdatedModel):
    '''Something that is on the program.'''
    title = models.CharField(max_length=255)
    description = models.TextField()
    event_type = models.ForeignKey(
        EventType)

class Speaker(CreatedUpdatedModel):
    '''Person anchoring an event.'''
    name = models.CharField(max_length=150)
    biography = models.TextField()
    picture = models.ImageField()
    events = models.ManyToManyField(
        Event,
        related_name='speakers',
        related_query_name='speaker')
