from program.consumers import ScheduleConsumer


channel_routing = [
    ScheduleConsumer.as_route(path=r"^/schedule/"),
]


