import irc3, re
from ircbot.models import OutgoingIrcMessage
from django.conf import settings
from django.utils import timezone
from events.models import Routing
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


@irc3.plugin
class Plugin(object):
    """BornHack IRC3 class"""

    requires = [
        'irc3.plugins.core', # makes the bot able to connect to an irc server and do basic irc stuff
        'irc3.plugins.userlist', # maintains a convenient list of the channels the bot is in and their users
    ]

    def __init__(self, bot):
        self.bot = bot


    ###############################################################################################
    ### builtin irc3 event methods

    def server_ready(self, **kwargs):
        """triggered after the server sent the MOTD (require core plugin)"""
        logger.debug("inside server_ready(), kwargs: %s" % kwargs)

        logger.info("Identifying with %s" % settings.IRCBOT_NICKSERV_MASK)
        self.bot.privmsg(settings.IRCBOT_NICKSERV_MASK, "identify %s %s" % (settings.IRCBOT_NICK, settings.IRCBOT_NICKSERV_PASSWORD))

        logger.info("Calling self.bot.get_outgoing_messages in %s seconds.." % settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS)
        self.bot.loop.call_later(settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS, self.bot.get_outgoing_messages)


    def connection_lost(self, **kwargs):
        """triggered when connection is lost"""
        logger.debug("inside connection_lost(), kwargs: %s" % kwargs)


    def connection_made(self, **kwargs):
        """triggered when connection is up"""
        logger.debug("inside connection_made(), kwargs: %s" % kwargs)


    ###############################################################################################
    ### decorated irc3 event methods

    @irc3.event(irc3.rfc.JOIN_PART_QUIT)
    def on_join_part_quit(self, **kwargs):
        """triggered when there is a join part or quit on a channel the bot is in"""
        logger.debug("inside on_join_part_quit(), kwargs: %s" % kwargs)


    @irc3.event(irc3.rfc.JOIN)
    def on_join(self, mask, channel, **kwargs):
        """Triggered when a channel is joined by someone, including the bot itself"""
        managed_channels = Routing.objects.filter(team__irc_channel=True, team__irc_channel_managed=True).values_list('team__irc_channel_name', flat=True).distinct()
        if mask.nick == self.bot.nick and channel in managed_channels:
            logger.debug("Just joined a channel I am supposed to be managing, asking ChanServ for info about %s" % channel)
            self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, "info %s" % channel)
            return


    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, **kwargs):
        """triggered when a privmsg is sent to the bot or to a channel the bot is in"""
        logger.debug("inside on_privmsg(), kwargs: %s" % kwargs)

        # we only handle NOTICEs for now
        if kwargs['event'] != "NOTICE":
            return

        # check if this is a message from nickserv
        if kwargs['mask'] == "NickServ!%s" % settings.IRCBOT_NICKSERV_MASK:
            if kwargs['data'] == '\x02%s\x02 is not a registered nickname.' % self.bot.nick:
                # the bots nickname is not registered, register new account with nickserv
                self.bot.privmsg(settings.IRCBOT_NICKSERV_MASK, "register %s %s" % (settings.IRCBOT_NICKSERV_PASSWORD, settings.IRCBOT_NICKSERV_EMAIL))
                return

        # check if this is a message from chanserv
        if kwargs['mask'] == "ChanServ!%s" % settings.IRCBOT_CHANSERV_MASK:
            logger.debug("got message from ChanServ")
            match = re.compile("Channel (#[a-zA-Z0-9-]+) is not registered.").match(kwargs['data'].replace("\x02", ""))
            if match:
                # the irc channel match.group(1) is not registered
                ircchannel = match.group(1)
                # get a list of the channels we are supposed to be managing
                managed_channels = list(Routing.objects.filter(team__irc_channel=True, team__irc_channel_managed=True).values_list('team__irc_channel_name', flat=True).distinct())
                if ircchannel in managed_channels:
                    logger.debug("ChanServ says channel %s is not registered, bot is supposed to be managing this channel, registering it with chanserv" % ircchannel)
                    self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, "register %s" % ircchannel)
                    return


    @irc3.event(irc3.rfc.KICK)
    def on_kick(self, **kwargs):
        logger.debug("inside on_kick(), kwargs: %s" % kwargs)


    ###############################################################################################
    ### custom irc3 methods

    @irc3.extend
    def get_outgoing_messages(self):
        """
            This method gets unprocessed OutgoingIrcMessage objects and attempts to send them to
            the target channel. Messages are skipped if the bot is not in the channel.
        """
        #logger.debug("inside get_outgoing_messages()")
        for msg in OutgoingIrcMessage.objects.filter(processed=False).order_by('created'):
            logger.info("processing irc message to %s: %s" % (msg.target, msg.message))
            # if this message expired mark it as expired and processed without doing anything
            if msg.timeout < timezone.now():
                logger.info("this message is expired, marking it as such instead of sending it to irc")
                msg.expired=True
                msg.processed=True
                msg.save()
                continue

            # is this message for a channel or a nick?
            if msg.target[0] == "#" and msg.target in self.bot.channels:
                logger.info("sending privmsg to %s: %s" % (msg.target, msg.message))
                self.bot.privmsg(msg.target, msg.message)
                msg.processed=True
                msg.save()
            elif msg.target:
                logger.info("sending privmsg to %s: %s" % (msg.target, msg.message))
                self.bot.privmsg(msg.target, msg.message)
                msg.processed=True
                msg.save()
            else:
                logger.warning("skipping message to %s" % msg.target)

        # call this function again in X seconds
        self.bot.loop.call_later(settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS, self.bot.get_outgoing_messages)

