from channels.generic.websockets import JsonWebsocketConsumer

from camps.models import Camp
from .models import EventInstance, Favorite, EventLocation, EventType


class ScheduleConsumer(JsonWebsocketConsumer):
    http_user = True

    def connection_groups(self, **kwargs):
        return ['schedule_users']

    def raw_receive(self, message, **kwargs):
        content = self.decode_json(message['text'])
        action = content.get('action')
        data = {}

        if action == 'init':
            camp_slug = content.get('camp_slug')
            try:
                camp = Camp.objects.get(slug=camp_slug)
                days = list(map(
                    lambda day:
                        { 'repr': day.lower.strftime('%A %Y-%m-%d')
                        , 'iso': day.lower.strftime('%Y-%m-%d')
                        , 'day_name': day.lower.strftime('%A')
                        },
                    camp.get_days('camp')
                ))
                event_instances_query_set = EventInstance.objects.filter(event__camp=camp)
                event_instances = list([x.to_json(user=message.user) for x in event_instances_query_set])

                event_locations_query_set = EventLocation.objects.filter(camp=camp)
                event_locations = list([x.to_json() for x in event_locations_query_set])

                event_types_query_set = EventType.objects.filter()
                event_types = list([x.to_json() for x in event_types_query_set])

                data = {
                    "event_locations": event_locations,
                    "event_types": event_types,
                    "accept": True,
                    "event_instances": event_instances,
                    "days": days,
                    "action": "init"
                }
            except Camp.DoesNotExist:
                pass

        if action == 'favorite':
            event_instance_id = content.get('event_instance_id')
            event_instance = EventInstance.objects.get(id=event_instance_id)
            Favorite.objects.create(
                user=message.user,
                event_instance=event_instance
            )

        if action == 'unfavorite':
            event_instance_id = content.get('event_instance_id')
            event_instance = EventInstance.objects.get(id=event_instance_id)
            favorite = Favorite.objects.get(event_instance=event_instance, user=message.user)
            favorite.delete()

        if data:
            self.send(data)

    def disconnect(self, message, **kwargs):
        pass
