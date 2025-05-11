import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger("bornhack.%s" % __name__)


def add_irc_message(target, message, timeout=10):
    """Convenience function for adding OutgoingIrcMessage objects.
    Defaults to a message timeout of 10 minutes
    """
    from .models import OutgoingIrcMessage

    OutgoingIrcMessage.objects.create(
        target=target,
        message=message,
        timeout=timezone.now() + timedelta(minutes=timeout),
    )
