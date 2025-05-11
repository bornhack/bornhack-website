import asyncio
import logging
import os
import re
import time

import irc3
from django.conf import settings
from django.utils import timezone

from ircbot.models import OutgoingIrcMessage
from teams.models import Team
from teams.models import TeamMember
from teams.utils import get_team_from_irc_channel

logger = logging.getLogger("bornhack.%s" % __name__)

# irc3 and django sitting in a tree
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@irc3.plugin
class Plugin:
    """BornHack IRC3 class"""

    requires = [
        "irc3.plugins.core",  # makes the bot able to connect to an irc server and do basic irc stuff
        "irc3.plugins.userlist",  # maintains a convenient list of the channels the bot is in and their users
    ]

    def __init__(self, bot):
        self.bot = bot

    ###############################################################################################
    # builtin irc3 event methods

    def server_ready(self, **kwargs):
        """Triggered after the server sent the MOTD (require core plugin)"""
        logger.debug("inside server_ready(), kwargs: %s" % kwargs)

        logger.info("Identifying with %s" % settings.IRCBOT_NICKSERV_MASK)
        self.bot.privmsg(
            settings.IRCBOT_NICKSERV_MASK,
            "identify %s %s" % (settings.IRCBOT_NICK, settings.IRCBOT_NICKSERV_PASSWORD),
        )

        logger.info(
            "Calling self.bot.do_stuff() in %s seconds.." % settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS,
        )
        asyncio.sleep(settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS)
        self.bot.do_stuff()

    def connection_lost(self, **kwargs):
        """Triggered when connection is lost"""
        logger.debug("inside connection_lost(), kwargs: %s" % kwargs)

    def connection_made(self, **kwargs):
        """Triggered when connection is up"""
        logger.debug("inside connection_made(), kwargs: %s" % kwargs)

    ###############################################################################################
    # decorated irc3 event methods

    @irc3.event(irc3.rfc.JOIN_PART_QUIT)
    def on_join_part_quit(self, **kwargs):
        """Triggered when there is a join part or quit on a channel the bot is in"""
        logger.debug("inside on_join_part_quit(), kwargs: %s" % kwargs)

        # TODO: on part or quit check if the bot is the only remaining member of a channel,
        # if so, check if the channel should be managed, and if so, part and join the channel
        # to gain @ and register with ChanServ

    @irc3.event(irc3.rfc.JOIN)
    def on_join(self, mask, channel, **kwargs):
        """Triggered when a channel is joined by someone, including the bot itself"""
        if mask.nick == self.bot.nick:
            # the bot just joined a channel
            if (
                channel in self.get_managed_team_channels()
                or channel == settings.IRCBOT_PUBLIC_CHANNEL
                or channel == settings.IRCBOT_VOLUNTEER_CHANNEL
            ):
                logger.debug(
                    "Just joined a channel I am supposed to be managing, asking ChanServ for info about %s" % channel,
                )
                self.get_channel_info(channel)
                return

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, **kwargs):
        """Triggered when a privmsg is sent to the bot or to a channel the bot is in"""
        # we only handle NOTICEs for now
        if kwargs["event"] != "NOTICE":
            return

        logger.debug("inside on_privmsg(), kwargs: %s" % kwargs)

        # check if this is a message from nickserv
        if kwargs["mask"] == "NickServ!%s" % settings.IRCBOT_NICKSERV_MASK:
            self.bot.handle_nickserv_privmsg(**kwargs)

        # check if this is a message from chanserv
        if kwargs["mask"] == "ChanServ!%s" % settings.IRCBOT_CHANSERV_MASK:
            self.bot.handle_chanserv_privmsg(**kwargs)

    @irc3.event(irc3.rfc.KICK)
    def on_kick(self, **kwargs):
        logger.debug("inside on_kick(), kwargs: %s" % kwargs)

    @irc3.event(irc3.rfc.MODE)
    def on_mode(self, **kwargs):
        """Triggered whenever a mode is changed."""
        logger.debug("inside on_mode(), kwargs: %s" % kwargs)

        # check if the bot just received @ in a channel which it is supposed to be managing
        if (
            kwargs["data"] == self.bot.nick
            and "o" in kwargs["modes"]
            and kwargs["target"] in self.get_managed_team_channels()
            and self.bot.nick in self.bot.channels[kwargs["target"]].modes["@"]
        ):
            # the bot has @ in this channel now, ask chanserv for info about it
            logger.debug(
                f"The bot just got +o aka @ in {kwargs['target']}, asking ChanServ for info about this channel, so it can be registered if needed...",
            )
            self.get_channel_info(kwargs["target"])

    ###############################################################################################
    # custom irc3 methods below here

    @irc3.extend
    def do_stuff(self):
        """Main periodic method called every N seconds."""
        # logger.debug("inside do_stuff()")

        # call the methods we need to
        self.bot.check_irc_channels()
        self.bot.fix_missing_acls()
        self.bot.get_outgoing_messages()

        # schedule a call of this function again in N seconds
        asyncio.sleep(settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS)
        self.bot.loop.call_later(
            settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS,
            self.bot.do_stuff,
        )

    @irc3.extend
    def get_outgoing_messages(self):
        """This method gets unprocessed OutgoingIrcMessage objects and attempts to send them to
        the target channel. Messages are skipped if the bot is not in the channel.
        """
        for msg in OutgoingIrcMessage.objects.filter(processed=False).order_by(
            "created",
        ):
            logger.info(f"processing irc message to {msg.target}: {msg.message}")
            # if this message expired mark it as expired and processed without doing anything
            if msg.timeout < timezone.now():
                logger.info(
                    "this message is expired, marking it as such instead of sending it to irc",
                )
                msg.expired = True
                msg.processed = True
                msg.save()
                continue

            # is this message for a channel or a nick?
            if (msg.target[0] == "#" and msg.target in self.bot.channels) or msg.target:
                logger.info(f"sending privmsg to {msg.target}: {msg.message}")
                self.bot.privmsg(msg.target, msg.message)
                msg.processed = True
                msg.save()
            else:
                logger.warning("skipping message to %s" % msg.target)

    ###############################################################################################
    # irc channel methods

    @irc3.extend
    def check_irc_channels(self):
        """Compare the list of IRC channels the bot is currently in with the list of IRC channels the bot is supposed to be in.
        Join or part channels as needed.
        """
        desired_channel_list = self.bot.get_desired_channel_list()
        # logger.debug("Inside check_irc_channels(), desired_channel_list is: %s and self.bot.channels is: %s" % (desired_channel_list, self.bot.channels.keys()))

        # loop over desired_channel_list, join as needed
        for channel in desired_channel_list:
            if channel not in self.bot.channels:
                logger.debug(
                    "I should be in %s but I am not, attempting to join..." % channel,
                )
                self.bot.join(channel)

        # loop over self.bot.channels, part as needed
        for channel in self.bot.channels:
            if channel not in desired_channel_list:
                logger.debug("I am in %s but I shouldn't be, parting..." % channel)
                self.bot.part(channel, "I am no longer needed here")

    @irc3.extend
    def get_desired_channel_list(self):
        """Return a list of strings of all the IRC channels the bot is supposed to be in"""
        desired_channel_list = self.get_managed_team_channels()
        desired_channel_list += self.get_unmanaged_team_channels()
        desired_channel_list.append(settings.IRCBOT_PUBLIC_CHANNEL)
        desired_channel_list.append(settings.IRCBOT_VOLUNTEER_CHANNEL)
        return desired_channel_list

    @irc3.extend
    def get_managed_team_channels(self):
        """Return a list of team IRC channels which the bot is supposed to be managing."""
        pubchans = Team.objects.filter(
            public_irc_channel_name__isnull=False,
            public_irc_channel_bot=True,
            public_irc_channel_managed=True,
        ).values_list("public_irc_channel_name", flat=True)

        privchans = Team.objects.filter(
            private_irc_channel_name__isnull=False,
            private_irc_channel_bot=True,
            private_irc_channel_managed=True,
        ).values_list("private_irc_channel_name", flat=True)

        return list(pubchans) + list(privchans)

    @irc3.extend
    def get_unmanaged_team_channels(self):
        """Return a list of team IRC channels which the bot is supposed to be in, but not managing."""
        pubchans = Team.objects.filter(
            public_irc_channel_name__isnull=False,
            public_irc_channel_bot=True,
            public_irc_channel_managed=False,
        ).values_list("public_irc_channel_name", flat=True)

        privchans = Team.objects.filter(
            private_irc_channel_name__isnull=False,
            private_irc_channel_bot=True,
            private_irc_channel_managed=False,
        ).values_list("private_irc_channel_name", flat=True)

        return list(pubchans) + list(privchans)

    @irc3.extend
    def setup_private_channel(self, channel):
        """Configures a private IRC channel by setting modes and adding all members to ACL if it is a team channel"""
        logger.debug("Inside setup_private_channel() for %s" % channel)

        # basic private channel modes
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, "SET %s mlock +inpst" % channel)
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, "SET %s SECURE on" % channel)
        self.bot.privmsg(
            settings.IRCBOT_CHANSERV_MASK,
            "SET %s RESTRICTED on" % channel,
        )

        # add the bot to the ACL
        self.bot.add_user_to_channel_acl(
            username=settings.IRCBOT_NICK,
            channel=channel,
            invite=True,
        )

        team = get_team_from_irc_channel(channel)
        if team:
            # this is a team channel, add team members to channel ACL
            self.bot.add_team_members_to_channel_acl(team)
            # make sure private_irc_channel_fix_needed is set to False and save
            team.private_irc_channel_fix_needed = False
            team.save()

    @irc3.extend
    def setup_public_channel(self, channel):
        """Configures a public IRC channel by setting modes and giving all team members +oO if it is a team channel"""
        logger.debug("Inside setup_public_channel() for %s" % channel)

        # basic private channel modes
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, "SET %s mlock +nt-lk" % channel)
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, "SET %s SECURE off" % channel)
        self.bot.privmsg(
            settings.IRCBOT_CHANSERV_MASK,
            "SET %s RESTRICTED off" % channel,
        )

        team = get_team_from_irc_channel(channel)
        if team:
            # add members to ACL
            self.bot.add_team_members_to_channel_acl(team)
            # make sure public_irc_channel_fix_needed is set to False and save
            team.public_irc_channel_fix_needed = False
            team.save()

    @irc3.extend
    def add_team_members_to_channel_acl(self, team):
        """Handles initial ACL for team channels.
        Sets membership.irc_acl_fix_needed=True for each approved teammember with a NickServ username
        """
        # add all members to the acl
        for membership in team.memberships.all():
            if membership.approved and membership.user.profile.nickserv_username:
                membership.irc_acl_fix_needed = True
                membership.save()

    @irc3.extend
    def add_user_to_channel_acl(self, username, channel, invite):
        """Add user to team IRC channel ACL"""
        # set autoop for this username
        self.bot.privmsg(
            settings.IRCBOT_CHANSERV_MASK,
            f"flags {channel} {username} +oO",
        )

        if invite:
            # also add autoinvite for this username
            self.bot.mode(channel, "+I", "$a:%s" % username)

        # add a delay so the bot doesn't flood itself off, irc3 antiflood settings do not help here, why?
        time.sleep(1)

    @irc3.extend
    def fix_missing_acls(self):
        """Called periodically by do_stuff()
        Loops over TeamMember objects and adds ACL entries as needed
        Loops over Team objects and fixes permissions and ACLS as needed
        """
        # first find all TeamMember objects which needs a loving hand
        missing_acls = TeamMember.objects.filter(irc_acl_fix_needed=True).exclude(
            user__profile__nickserv_username="",
        )

        # loop over them and fix what needs to be fixed
        if missing_acls:
            logger.debug(
                "Found %s memberships which need IRC ACL fixing.." % missing_acls.count(),
            )
            for membership in missing_acls:
                # add to team public channel?
                if membership.team.public_irc_channel_name and membership.team.public_irc_channel_managed:
                    self.bot.add_user_to_channel_acl(
                        username=membership.user.profile.nickserv_username,
                        channel=membership.team.public_irc_channel_name,
                        invite=False,
                    )

                # add to team private channel?
                if membership.team.private_irc_channel_name and membership.team.private_irc_channel_managed:
                    self.bot.add_user_to_channel_acl(
                        username=membership.user.profile.nickserv_username,
                        channel=membership.team.private_irc_channel_name,
                        invite=True,
                    )

                # add to volunteer channel
                self.bot.add_user_to_channel_acl(
                    username=membership.user.profile.nickserv_username,
                    channel=settings.IRCBOT_VOLUNTEER_CHANNEL,
                    invite=True,
                )

                # mark membership as irc_acl_fix_needed=False and save
                membership.irc_acl_fix_needed = False
                membership.save()

        # loop over teams where the private channel needs fixing
        for team in Team.objects.filter(private_irc_channel_fix_needed=True):
            logger.debug(
                "Team %s private IRC channel %s needs ACL fixing" % (team, team.private_irc_channel_name),
            )
            self.bot.setup_private_channel(team.private_irc_channel_name)

        # loop over teams where the public channel needs fixing
        for team in Team.objects.filter(public_irc_channel_fix_needed=True):
            logger.debug(
                "Team %s public IRC channel %s needs ACL fixing" % (team, team.public_irc_channel_name),
            )
            self.bot.setup_public_channel(team.public_irc_channel_name)

    ###############################################################################################
    # services (ChanServ & NickServ) methods

    @irc3.extend
    def handle_chanserv_privmsg(self, **kwargs):
        """Handle messages from ChanServ on networks with Services."""
        logger.debug("Got a message from ChanServ")

        ###############################################
        # handle "Channel \x02#example\x02 is not registered." message
        ###############################################
        match = re.compile("Channel (#[a-zA-Z0-9-]+) is not registered.").match(
            kwargs["data"].replace("\x02", ""),
        )
        if match:
            # the irc channel is not registered
            channel = match.group(1)
            # get a list of the channels we are supposed to be managing
            if channel in self.bot.get_managed_team_channels() or channel == settings.IRCBOT_VOLUNTEER_CHANNEL:
                # we want to register this channel! though we can only do so if we have a @ in the channel
                if self.bot.nick in self.bot.channels[channel].modes["@"]:
                    logger.debug(
                        "ChanServ says channel %s is not registered, bot is supposed to be managing this channel, registering it with chanserv"
                        % channel,
                    )
                    self.bot.privmsg(
                        settings.IRCBOT_CHANSERV_MASK,
                        "register %s" % channel,
                    )
                else:
                    logger.debug(
                        "ChanServ says channel %s is not registered, bot is supposed to be managing this channel, but the bot cannot register without @ in the channel"
                        % channel,
                    )
                    self.bot.privmsg(
                        channel,
                        "I need @ before I can register this channel with ChanServ",
                    )
            return

        ###############################################
        # handle "\x02#example\x02 is now registered to \x02tykbhdev\x02" message
        ###############################################
        match = re.compile(
            "(#[a-zA-Z0-9-]+) is now registered to ([a-zA-Z0-9-]+)\\.",
        ).match(kwargs["data"].replace("\x02", ""))
        if match:
            # the irc channel is now registered
            channel = match.group(1)
            logger.debug(
                "Channel %s was registered with ChanServ, looking up Team..." % channel,
            )

            team = get_team_from_irc_channel(channel)
            if team:
                if team.private_irc_channel_name == channel:
                    # set private channel modes, +I and ACL
                    self.bot.setup_private_channel(channel)
                else:
                    # set public channel modes and +oO for all members
                    self.bot.setup_public_channel(channel)
                return
            logger.debug("Unable to find Team matching IRC channel %s" % channel)

            # check if this channel is the volunteer channel
            if channel == settings.IRCBOT_VOLUNTEER_CHANNEL:
                logger.debug("%s is the volunteer channel, setting up" % channel)
                self.bot.setup_private_channel(channel)
                # lets handle the volunteer channels initial ACL manually..
                return

        logger.debug("Unhandled ChanServ message: %s" % kwargs["data"])

    @irc3.extend
    def handle_nickserv_privmsg(self, **kwargs):
        """Handles messages from NickServ on networks with Services."""
        logger.debug("Got a message from NickServ")

        # handle "\x02botnick\x02 is not a registered nickname." message
        if kwargs["data"] == "\x02%s\x02 is not a registered nickname." % self.bot.nick:
            # the bots nickname is not registered, register new account with nickserv
            self.bot.privmsg(
                settings.IRCBOT_NICKSERV_MASK,
                "register %s %s" % (settings.IRCBOT_NICKSERV_PASSWORD, settings.IRCBOT_NICKSERV_EMAIL),
            )
            return

        logger.debug("Unhandled NickServ message: %s" % kwargs["data"])

    @irc3.extend
    def get_channel_info(self, channel):
        """Ask ChanServ for info about a channel."""
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, f"info {channel}")
