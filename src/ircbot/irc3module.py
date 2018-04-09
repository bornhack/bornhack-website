import irc3, re
from ircbot.models import OutgoingIrcMessage
from teams.models import Team, TeamMember
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

        logger.info("Calling self.bot.do_stuff() in %s seconds.." % settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS)
        self.bot.loop.call_later(settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS, self.bot.do_stuff)


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

        # TODO: on part or quit check if the bot is the only remaining member of a channel,
        # if so, check if the channel should be managed, and if so, part and join the channel
        # to gain @ and register with ChanServ


    @irc3.event(irc3.rfc.JOIN)
    def on_join(self, mask, channel, **kwargs):
        """Triggered when a channel is joined by someone, including the bot itself"""
        if mask.nick == self.bot.nick:
            # the bot just joined a channel
            if channel in self.get_managed_team_channels():
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
            self.bot.handle_nickserv_privmsg(**kwargs)

        # check if this is a message from chanserv
        if kwargs['mask'] == "ChanServ!%s" % settings.IRCBOT_CHANSERV_MASK:
            self.bot.handle_chanserv_privmsg(**kwargs)


    @irc3.event(irc3.rfc.KICK)
    def on_kick(self, **kwargs):
        logger.debug("inside on_kick(), kwargs: %s" % kwargs)


    ###############################################################################################
    ### custom irc3 methods

    @irc3.extend
    def do_stuff(self):
        """
        Main periodic method called every N seconds.
        """
        #logger.debug("inside do_stuff()")

        # call the methods we need to
        self.bot.check_irc_channels()
        self.bot.fix_missing_acls()
        self.bot.get_outgoing_messages()

        # schedule a call of this function again in N seconds
        self.bot.loop.call_later(settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS, self.bot.do_stuff)


    @irc3.extend
    def get_outgoing_messages(self):
        """
            This method gets unprocessed OutgoingIrcMessage objects and attempts to send them to
            the target channel. Messages are skipped if the bot is not in the channel.
        """
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


    ###############################################################################################
    ### irc channel methods

    @irc3.extend
    def check_irc_channels(self):
        """
        Compare the list of IRC channels the bot is currently in with the list of IRC channels the bot is supposed to be in.
        Join or part channels as needed.
        """
        desired_channel_list = list(set(list(self.get_managed_team_channels()) + list(self.get_unmanaged_team_channels()) + [settings.IRCBOT_PUBLIC_CHANNEL]))
        #logger.debug("Inside check_irc_channels(), desired_channel_list is: %s and self.bot.channels is: %s" % (desired_channel_list, self.bot.channels.keys()))

        # loop over desired_channel_list, join as needed
        for channel in desired_channel_list:
            if channel not in self.bot.channels:
                logger.debug("I should be in %s but I am not, attempting to join..." % channel)
                self.bot.join(channel)

        # loop over self.bot.channels, part as needed
        for channel in self.bot.channels:
            if channel not in desired_channel_list:
                logger.debug("I am in %s but I shouldn't be, parting..." % channel)
                self.bot.part(channel, "I am no longer needed here")


    @irc3.extend
    def get_managed_team_channels(self):
        """
        Return a unique list of team IRC channels which the bot is supposed to be managing.
        """
        return Team.objects.filter(
            irc_channel=True,
            irc_channel_managed=True
        ).values_list("irc_channel_name", flat=True)


    @irc3.extend
    def get_unmanaged_team_channels(self):
        """
        Return a unique list of team IRC channels which the bot is not supposed to be managing.
        """
        return Team.objects.filter(
            irc_channel=True,
            irc_channel_managed=False
        ).values_list("irc_channel_name", flat=True)


    @irc3.extend
    def setup_private_channel(self, team):
        """
        Configures a private team IRC channel by setting modes and adding all members to ACL
        """
        # basic private channel modes
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, "SET %s mlock +inpst" % team.irc_channel_name)
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, "SET %s SECURE on" % team.irc_channel_name)
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, "SET %s RESTRICTED on" % team.irc_channel_name)

        # add the bot to the ACL
        self.bot.add_user_to_team_channel_acl(
            username=settings.IRCBOT_NICK,
            channel=team.irc_channel_name
        )

        # add all members to the acl
        for membership in team.memberships.all():
            if membership.approved and membership.user.profile.nickserv_username:
                self.bot.add_user_to_team_channel_acl(
                    username=membership.user.profile.nickserv_username,
                    channel=membership.team.irc_channel_name,
                )

                # mark membership as irc_channel_acl_ok=True and save
                membership.irc_channel_acl_ok=True
                membership.save()


    @irc3.extend
    def add_user_to_team_channel_acl(self, username, channel):
        """
        Add user to team IRC channel ACL
        """
        # set autoop for this username
        self.bot.privmsg(
            settings.IRCBOT_CHANSERV_MASK,
            "flags %(channel)s %(user)s +oO" % {
                'channel': channel,
                'user': username,
            },
        )

        # also add autoinvite for this username
        self.bot.mode(channel, '+I', '$a:%s' % username)


    @irc3.extend
    def fix_missing_acls(self):
        """
        Called periodically by do_stuff()
        Loops over TeamMember objects and adds and removes ACL entries as needed
        """
        missing_acls = TeamMember.objects.filter(
            team__irc_channel=True,
            team__irc_channel_managed=True,
            team__irc_channel_private=True,
            irc_channel_acl_ok=False
        ).exclude(
            user__profile__nickserv_username=''
        )

        if not missing_acls:
            return

        logger.debug("Found %s memberships which need IRC ACL fixing.." % missing_acls.count())
        for membership in missing_acls:
            self.bot.add_user_to_team_channel_acl(
                username=membership.user.profile.nickserv_username,
                channel=membership.team.irc_channel_name,
            )
            # mark membership as irc_channel_acl_ok=True and save
            membership.irc_channel_acl_ok=True
            membership.save()


    ###############################################################################################
    ### services (ChanServ & NickServ) methods

    @irc3.extend
    def handle_chanserv_privmsg(self, **kwargs):
        """
        Handle messages from ChanServ on networks with Services.
        """
        logger.debug("Got a message from ChanServ")

        ###############################################
        # handle "Channel \x02#example\x02 is not registered." message
        ###############################################
        match = re.compile("Channel (#[a-zA-Z0-9-]+) is not registered.").match(kwargs['data'].replace("\x02", ""))
        if match:
            # the irc channel is not registered
            channel = match.group(1)
            # get a list of the channels we are supposed to be managing
            if channel in self.bot.get_managed_team_channels():
                # we want to register this channel! but we can only do so if we have a @ in the channel
                if self.bot.nick in self.bot.channels[channel].modes['@']:
                    logger.debug("ChanServ says channel %s is not registered, bot is supposed to be managing this channel, registering it with chanserv" % channel)
                    self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, "register %s" % channel)
                else:
                    logger.debug("ChanServ says channel %s is not registered, bot is supposed to be managing this channel, but the bot cannot register without @ in the channel" % channel)
                    self.bot.privmsg(channel, "I need @ before I can register this channel with ChanServ")
            return

        ###############################################
        # handle "\x02#example\x02 is now registered to \x02tykbhdev\x02" message
        ###############################################
        match = re.compile("(#[a-zA-Z0-9-]+) is now registered to ([a-zA-Z0-9-]+)\\.").match(kwargs['data'].replace("\x02", ""))
        if match:
            # the irc channel is now registered
            channel = match.group(1)
            botnick = match.group(2)
            logger.debug("Channel %s was registered with ChanServ, looking up Team..." % channel)

            # if this channel is a private team IRC channel set modes and add initial ACL
            try:
                team = Team.objects.get(irc_channel_name=channel)
            except Team.DoesNotExist:
                logger.debug("Unable to find Team matching IRC channel %s" % channel)
                return

            if not team.irc_channel_private:
                # this channel is not private, no mode change and ACL needed
                return

            # set channel modes and ACL
            self.bot.setup_private_channel(team)
            return

        logger.debug("Unhandled ChanServ message: %s" % kwargs['data'])


    @irc3.extend
    def handle_nickserv_privmsg(self, **kwargs):
        """th
        Handles messages from NickServ on networks with Services.
        """
        logger.debug("Got a message from NickServ")

        # handle "\x02botnick\x02 is not a registered nickname." message
        if kwargs['data'] == '\x02%s\x02 is not a registered nickname.' % self.bot.nick:
            # the bots nickname is not registered, register new account with nickserv
            self.bot.privmsg(settings.IRCBOT_NICKSERV_MASK, "register %s %s" % (settings.IRCBOT_NICKSERV_PASSWORD, settings.IRCBOT_NICKSERV_EMAIL))
            return

        logger.debug("Unhandled NickServ message: %s" % kwargs['data'])

