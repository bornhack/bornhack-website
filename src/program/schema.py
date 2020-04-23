import graphene
from graphene import Field, NonNull, List
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Event
from .models import EventSlot
from .models import EventLocation
from .models import EventTrack
from .models import EventType
from .models import Speaker
from .models import Url
from .models import UrlType


class EventTypeNode(DjangoObjectType):
    class Meta:
        model = EventType
        filter_fields = {"name": ["iexact"]}


class EventLocationNode(DjangoObjectType):
    class Meta:
        model = EventLocation
        filter_fields = {"name": ["iexact"], "camp__slug": ["iexact"]}


class EventTrackNode(DjangoObjectType):
    class Meta:
        model = EventTrack
        filter_fields = {"name": ["iexact"], "camp__slug": ["iexact"]}


class EventSlotNode(DjangoObjectType):

    start = graphene.Int(
        required=True,
        description="When this instance of the event starts. In posix time.",
    )
    end = graphene.Int(
        required=True,
        description="When this instance of the event ends. In posix time.",
    )

    class Meta:
        model = EventSlot
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
        only_fields = ("id", "name", "biography", "slug", "camp", "events")
        filter_fields = {"name": ["iexact"], "camp__slug": ["iexact"]}


class EventNode(DjangoObjectType):
    class Meta:
        model = Event
        filter_fields = {"title": ["iexact"], "track__camp__slug": ["iexact"]}


class UrlNode(DjangoObjectType):
    class Meta:
        model = Url
        only_fields = ("url", "url_type")


class UrlTypeNode(DjangoObjectType):
    class Meta:
        model = UrlType


class ProgramQuery(object):
    all_event_types = NonNull(List(NonNull(EventTypeNode)))

    def resolve_all_event_types(self, info, **kwargs):
        return EventType.objects.all()

    all_event_locations = NonNull(List(NonNull(EventLocationNode)))

    def resolve_all_event_locations(self, info, **kwargs):
        return EventLocation.objects.all()

    all_event_tracks = NonNull(List(NonNull(EventTrackNode)))

    def resolve_all_event_tracks(self, info, **kwargs):
        return EventTrack.objects.all()

    all_event_slots = NonNull(List(NonNull(EventSlotNode)))

    def resolve_all_event_slots(self, info, **kwargs):
        return EventSlot.objects.all()

    all_events = NonNull(List(NonNull(EventNode)))

    def resolve_all_events(self, info, **kwargs):
        return Event.objects.all()

    all_speakers = NonNull(List(NonNull(SpeakerNode)))

    def resolve_all_speakers(self, info, **kwargs):
        return Event.objects.all()
