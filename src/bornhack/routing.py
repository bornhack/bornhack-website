from django.conf.urls import url

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from program.consumers import ScheduleConsumer


application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter([url(r"^schedule/", ScheduleConsumer)])
        )
    }
)
