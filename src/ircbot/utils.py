from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger(f"bornhack.{__name__}")


def add_irc_message(target, message, timeout=10) -> None:
    """Convenience function for adding OutgoingIrcMessage objects.
    Defaults to a message timeout of 10 minutes.
    """
    from .models import OutgoingIrcMessage

    OutgoingIrcMessage.objects.create(
        target=target,
        message=message,
        timeout=timezone.now() + timedelta(minutes=timeout),
    )
