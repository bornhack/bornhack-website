from __future__ import annotations

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter
from django.urls import path

from program.consumers import ScheduleConsumer

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter([path("schedule/", ScheduleConsumer)]),
        ),
    },
)
