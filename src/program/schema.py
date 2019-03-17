from graphene import relay

from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import (
    Event,
    EventType,
    EventLocation,
    EventTrack,
    EventInstance,
    Speaker,
)


class EventTypeNode(DjangoObjectType):
    class Meta:
        model = EventType
        interfaces = (relay.Node, )
        filter_fields = {
            'name': ['iexact'],
        }


class EventLocationNode(DjangoObjectType):
    class Meta:
        model = EventLocation
        interfaces = (relay.Node, )
        filter_fields = {
            'name': ['iexact'],
        }


class EventTrackNode(DjangoObjectType):
    class Meta:
        model = EventTrack
        interfaces = (relay.Node, )
        filter_fields = {
            'name': ['iexact'],
        }


class EventInstanceNode(DjangoObjectType):

    class Meta:
        model = EventInstance
        interfaces = (relay.Node, )
        filter_fields = {
            'event__title': ['iexact'],
        }

    def resolve_when(self, info):
        # We need to resolve this ourselves, graphene-django isn't smart enough
        return [self.when.lower, self.when.upper]


class SpeakerNode(DjangoObjectType):
    class Meta:
        model = Speaker
        interfaces = (relay.Node, )
        only_fields = ('id', 'name', 'biography', 'slug', 'camp', 'events')
        filter_fields = {
            'name': ['iexact'],
        }


class EventNode(DjangoObjectType):
    class Meta:
        model = Event
        interfaces = (relay.Node, )
        filter_fields = {
            'title': ['iexact'],
            'track__camp__slug': ['iexact'],
        }


class ProgramQuery(object):
    event_type = relay.Node.Field(EventTypeNode)
    all_event_types = DjangoFilterConnectionField(EventTypeNode)

    event_location = relay.Node.Field(EventLocationNode)
    all_event_locations = DjangoFilterConnectionField(EventLocationNode)

    event_track = relay.Node.Field(EventTrackNode)
    all_event_tracks = DjangoFilterConnectionField(EventTrackNode)

    event_instance = relay.Node.Field(EventInstanceNode)
    all_event_instances = DjangoFilterConnectionField(EventInstanceNode)

    event = relay.Node.Field(EventNode)
    all_events = DjangoFilterConnectionField(EventNode)

    speaker = relay.Node.Field(SpeakerNode)
    all_speakers = DjangoFilterConnectionField(SpeakerNode)

