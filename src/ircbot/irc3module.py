import irc3
from ircbot.models import OutgoingIrcMessage
from django.conf import settings
from django.utils import timezone


@irc3.plugin
class Plugin(object):
    """BornHack IRC3 class"""

    requires = [
        'irc3.plugins.core', # makes the bot able to connect to an irc server and do basic irc stuff
        'irc3.plugins.userlist', # maintains a convenient list of the channels the bot is in and their users
        'irc3.plugins.command', # what does this do?
    ]

    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.log


    ###############################################################################################
    ### builtin irc3 event methods

    def server_ready(self, **kwargs):
        """triggered after the server sent the MOTD (require core plugin)"""
        if settings.DEBUG:
            print("inside server_ready(), kwargs: %s" % kwargs)


    def connection_lost(self, **kwargs):
        """triggered when connection is lost"""
        if settings.DEBUG:
            print("inside connection_lost(), kwargs: %s" % kwargs)


    def connection_made(self, **kwargs):
        """triggered when connection is up"""
        if settings.DEBUG:
            print("inside connection_made(), kwargs: %s" % kwargs)


    ###############################################################################################
    ### decorated irc3 event methods

    @irc3.event(irc3.rfc.JOIN_PART_QUIT)
    def on_join_part_quit(self, **kwargs):
        """triggered when there is a join part or quit on a channel the bot is in"""
        if settings.DEBUG:
            print("inside on_join_part_quit(), kwargs: %s" % kwargs)
        if self.bot.nick == kwargs['mask'].split("!")[0] and kwargs['channel'] == "#tirsdagsfilm":
            self.bot.loop.call_later(1, self.bot.get_outgoing_messages)


    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, **kwargs):
        """triggered when a privmsg is sent to the bot or to a channel the bot is in"""
        if settings.DEBUG:
            print("inside on_privmsg(), kwargs: %s" % kwargs)


    @irc3.event(irc3.rfc.KICK)
    def on_kick(self, **kwargs):
        if settings.DEBUG:
            print("inside on_kick(), kwargs: %s" % kwargs)

    ###############################################################################################
    ### custom irc3 methods

    @irc3.extend
    def get_outgoing_messages(self):
        """
            This method gets unprocessed OutgoingIrcMessage objects and attempts to send them to
            the target channel. Messages are skipped if the bot is not in the channel.
        """
        print("inside get_outgoing_messages()")
        for msg in OutgoingIrcMessage.objects.filter(processed=False).order_by('created'):
            # if this message expired mark it as expired and processed without doing anything
            if msg.timeout < timezone.now():
                # this message is expired
                msg.expired=True
                msg.processed=True
                msg.save()
                continue

            # is this message for a channel or a nick?
            if msg.target[0] == "#" and msg.target in self.bot.channels:
                print("sending privmsg to %s: %s" % (msg.target, msg.message))
                self.bot.privmsg(msg.target, msg.message)
                msg.processed=True
                msg.save()
            elif msg.target:
                self.bot.privmsg(msg.target, msg.message)
                msg.processed=True
                msg.save()
            else:
                print("skipping message to %s" % msg.target)

        # call this function again in 60 seconds
        self.bot.loop.call_later(settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS, self.bot.get_outgoing_messages)


