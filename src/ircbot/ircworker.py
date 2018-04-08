from django.conf import settings
import logging
import irc3
from events.models import Routing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bornhack.%s' % __name__)


def do_work():
    """
        Run irc3 module code, wait for events on IRC and wait for messages in OutgoingIrcMessage
    """
    if hasattr(settings, 'IRCBOT_CHANNELS'):
        logger.error("settings.IRCBOT_CHANNELS is deprecated. Please define settings.IRCBOT_PUBLIC_CHANNEL and use team channels for the rest.")
        return False

    config = {
        'nick': settings.IRCBOT_NICK,
        'autojoins': [],
        'host': settings.IRCBOT_SERVER_HOSTNAME,
        'port': settings.IRCBOT_SERVER_PORT,
        'ssl': settings.IRCBOT_SERVER_USETLS,
        'timeout': 30,
        'includes': [
            'ircbot.irc3module',
        ],
    }
    logger.debug("Connecting to IRC with the following config: %s" % config)
    try:
        irc3.IrcBot(**config).run(forever=True)
    except Exception as E:
        logger.exception("Got exception inside do_work for %s" % self.workermodule)
        raise E

