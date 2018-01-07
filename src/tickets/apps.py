from django.apps import AppConfig
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class TicketsConfig(AppConfig):
    name = 'tickets'
