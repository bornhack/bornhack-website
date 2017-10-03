from django.apps import AppConfig
from .signal_handlers import ticket_created
from django.db.models.signals import post_save
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class TicketsConfig(AppConfig):
    name = 'tickets'

    def ready(self):
        post_save.connect(ticket_created, sender='tickets.ShopTicket')

