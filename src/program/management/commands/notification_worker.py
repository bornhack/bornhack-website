from __future__ import annotations

import logging
from datetime import timedelta
from time import sleep

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from camps.utils import get_current_camp
from ircbot.models import OutgoingIrcMessage
from program.models import EventInstance

logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    args = "none"
    help = "Queue notifications for channels and users for upcoming event instances."

    def output(self, message) -> None:
        self.stdout.write(
            "{}: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message),
        )

    def handle(self, *args, **options) -> None:
        self.output("Schedule notification worker running...")
        while True:
            camp = get_current_camp()
            if camp:
                # a camp is currently going on, check if we need to send out any notifications
                for ei in EventInstance.objects.filter(
                    event__camp=camp,
                    event__event_type__notifications=True,
                    notifications_sent=False,
                    when__startswith__lt=timezone.now()
                    + timedelta(
                        minutes=settings.SCHEDULE_EVENT_NOTIFICATION_MINUTES,
                    ),  # start of event is less than X minutes away
                    when__startswith__gt=timezone.now(),  # but event has not started yet
                ):
                    # this event is less than settings.SCHEDULE_EVENT_NOTIFICATION_MINUTES minutes from starting, queue an IRC notificatio
                    oim = OutgoingIrcMessage.objects.create(
                        target=settings.IRCBOT_SCHEDULE_ANNOUNCE_CHANNEL,
                        message=f"starting soon: {ei}",
                        timeout=ei.when.lower,
                    )
                    logger.info(
                        f"added irc message id {oim.id} for eventinstance {ei}",
                    )
                    ei.notifications_sent = True
                    ei.save()

            # check once per minute
            sleep(60)
