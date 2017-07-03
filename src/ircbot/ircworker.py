from .models import OutgoingIrcMessage
from django.conf import settings
import logging, irc3
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bornhack.%s' % __name__)


def do_work():
    """
        Run irc3 module code, wait for events on IRC and wait for messages in OutgoingIrcMessage
    """
    config = {
        'nick': settings.IRCBOT_NICK,
        'autojoins': list(set(settings.IRCBOT_CHANNELS.values())),
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
        raise

