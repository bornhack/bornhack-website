from django.apps import AppConfig
from django.db.models.signals import post_save
from .signals import ticket_changed
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class TicketsConfig(AppConfig):
    name = 'tickets'

    def ready(self):
        # connect the post_save signal, including a dispatch_uid to prevent it being called multiple times in corner cases
        post_save.connect(ticket_changed, sender='models.ShopTicket', dispatch_uid='shopticket_save_signal')

