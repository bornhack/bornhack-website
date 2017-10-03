from django.apps import AppConfig
import logging
logger = logging.getLogger("bornhack.%s" % __name__)

class ShopConfig(AppConfig):
    name = 'shop'

