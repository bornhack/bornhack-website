from __future__ import annotations

import logging

from django.apps import AppConfig

logger = logging.getLogger("bornhack.%s" % __name__)


class TicketsConfig(AppConfig):
    name = "tickets"

    def ready(self):
        pass
