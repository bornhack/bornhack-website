from channels.generic.websocket import JsonWebsocketConsumer

from camps.models import Camp
from .models import (
    Event,
    EventInstance,
    Favorite,
    EventLocation,
    EventType,
    Speaker
)


class ScheduleConsumer(JsonWebsocketConsumer):
    groups = ['schedule_users']

    def receive(self, text_data, **kwargs):
        user = self.scope['user']
        content = self.decode_json(text_data)
        action = content.get('action')
        data = {}

        if action == 'init':
            camp_slug = content.get('camp_slug')
            try:
                camp = Camp.objects.get(slug=camp_slug)
                days = list(map(
                    lambda day:
                        {
                            'repr': day.lower.strftime('%A %Y-%m-%d'),
                            'iso': day.lower.strftime('%Y-%m-%d'),
                            'day_name': day.lower.strftime('%A'),
                        },
                    camp.get_days('camp')
                ))

                events_query_set = Event.objects.filter(track__camp=camp)
                events = list([x.serialize() for x in events_query_set])

                event_instances_query_set = EventInstance.objects.filter(
                    event__track__camp=camp
                )
                event_instances = list([
                    x.serialize(user=user)
                    for x in event_instances_query_set
                ])

                event_locations_query_set = EventLocation.objects.filter(
                    camp=camp
                )
                event_locations = list([
                    x.serialize()
                    for x in event_locations_query_set
                ])

                event_types_query_set = EventType.objects.filter()
                event_types = list([
                    x.serialize()
                    for x in event_types_query_set
                ])

                speakers_query_set = Speaker.objects.filter(camp=camp)
                speakers = list([x.serialize() for x in speakers_query_set])

                data = {
                    "action": "init",
                    "events": events,
                    "event_instances": event_instances,
                    "event_locations": event_locations,
                    "event_types": event_types,
                    "speakers": speakers,
                    "days": days,
                }
            except Camp.DoesNotExist:
                pass

        if action == 'favorite':
            event_instance_id = content.get('event_instance_id')
            event_instance = EventInstance.objects.get(id=event_instance_id)
            Favorite.objects.create(
                user=user,
                event_instance=event_instance
            )

        if action == 'unfavorite':
            try:
                event_instance_id = content.get('event_instance_id')
                event_instance = EventInstance.objects.get(
                    id=event_instance_id
                )
                favorite = Favorite.objects.get(
                    event_instance=event_instance,
                    user=user
                )
                favorite.delete()
            except Favorite.DoesNotExist:
                # We don't want to do anything.
                return

        if data:
            self.send_json(data)

    def disconnect(self, message, **kwargs):
        pass
