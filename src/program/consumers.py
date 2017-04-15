from channels.generic.websockets import JsonWebsocketConsumer

from .models import EventInstance


class ScheduleConsumer(JsonWebsocketConsumer):
    http_user = True

    def connection_groups(self, **kwargs):
        return ['schedule_users']

    def connect(self, message, **kwargs):
        self.send({"accept": True})

    def receive(self, content, **kwargs):
        action = content.get('action')
        data = {}

        if action == 'get_event_instance':
            event_instance_id = content.get('event_instance_id')
            event_instance = EventInstance.objects.get(id=event_instance_id)
            data['action'] = 'event_instance'
            data['event_instance'] = event_instance.to_json()

        self.send(data)

    def disconnect(self, message, **kwargs):
        pass
