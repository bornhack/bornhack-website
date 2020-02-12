import logging

from django.apps import AppConfig

logger = logging.getLogger("bornhack.%s" % __name__)


class ShopConfig(AppConfig):
    name = "shop"
