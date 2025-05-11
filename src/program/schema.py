from __future__ import annotations

import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Event
from .models import EventInstance
from .models import EventLocation
from .models import EventTrack
from .models import EventType
from .models import Speaker
from .models import Url
from .models import UrlType


class EventTypeNode(DjangoObjectType):
    class Meta:
        model = EventType
        interfaces = (relay.Node,)
        filter_fields = {"name": ["iexact"]}


class EventLocationNode(DjangoObjectType):
    class Meta:
        model = EventLocation
        interfaces = (relay.Node,)
        filter_fields = {"name": ["iexact"], "camp__slug": ["iexact"]}


class EventTrackNode(DjangoObjectType):
    class Meta:
        model = EventTrack
        interfaces = (relay.Node,)
        filter_fields = {"name": ["iexact"], "camp__slug": ["iexact"]}


class EventInstanceNode(DjangoObjectType):
    start = graphene.Int(
        required=True,
        description="When this instance of the event starts. In posix time.",
    )
    end = graphene.Int(
        required=True,
        description="When this instance of the event ends. In posix time.",
    )

    class Meta:
        model = EventInstance
        interfaces = (relay.Node,)
        only_fields = ("event", "start", "end", "location")
        filter_fields = {
            "event__title": ["iexact"],
            "event__track__camp__slug": ["iexact"],
        }

    def resolve_start(self, info, **kwargs):
        return self.when.lower.timestamp()

    def resolve_end(self, info, **kwargs):
        return self.when.upper.timestamp()


class SpeakerNode(DjangoObjectType):
    class Meta:
        model = Speaker
        interfaces = (relay.Node,)
        only_fields = ("id", "name", "biography", "slug", "camp", "events")
        filter_fields = {"name": ["iexact"], "camp__slug": ["iexact"]}


class EventNode(DjangoObjectType):
    class Meta:
        model = Event
        interfaces = (relay.Node,)
        filter_fields = {"title": ["iexact"], "track__camp__slug": ["iexact"]}


class UrlNode(DjangoObjectType):
    class Meta:
        model = Url
        interfaces = (relay.Node,)
        only_fields = ("url", "url_type")


class UrlTypeNode(DjangoObjectType):
    class Meta:
        model = UrlType
        interfaces = (relay.Node,)


class ProgramQuery:
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

    url = relay.Node.Field(UrlNode)
    url_type = relay.Node.Field(UrlTypeNode)
