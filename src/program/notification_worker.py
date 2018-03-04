from django.conf import settings
from django.utils import timezone
from ircbot.models import OutgoingIrcMessage
from camps.utils import get_current_camp
from program.models import EventInstance
from datetime import timedelta
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def do_work():
    """
        The notification worker sends irc messages for upcomming events
    """
    camp = get_current_camp()
    if camp:
        # a camp is currently going on, check if we need to send out any notifications
        for ei in EventInstance.objects.filter(
            event__camp=camp,
            event__event_type__notifications=True,
            notifications_sent=False,
            when__startswith__lt=timezone.now()+timedelta(minutes=settings.SCHEDULE_EVENT_NOTIFICATION_MINUTES),  # start of event is less than X minutes away
            when__startswith__gt=timezone.now()  # but event has not started yet
        ):
            # this event is less than settings.SCHEDULE_EVENT_NOTIFICATION_MINUTES minutes from starting, queue an IRC notificatio
            oim = OutgoingIrcMessage.objects.create(
                target=settings.IRCBOT_SCHEDULE_ANNOUNCE_CHANNEL,
                message="starting soon: %s" % ei,
                timeout=ei.when.lower
            )
            logger.info(
                "added irc message id %s for eventinstance %s" % (oim.id, ei)
            )
            ei.notifications_sent = True
            ei.save()
