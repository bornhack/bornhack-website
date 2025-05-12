from __future__ import annotations

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

logger = logging.getLogger(f"bornhack.{__name__}")

# irc3 and django sitting in a tree
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@irc3.plugin
class Plugin:
    """BornHack IRC3 class."""

    requires = [
        "irc3.plugins.core",  # makes the bot able to connect to an irc server and do basic irc stuff
        "irc3.plugins.userlist",  # maintains a convenient list of the channels the bot is in and their users
    ]

    def __init__(self, bot) -> None:
        self.bot = bot

    ###############################################################################################
    # builtin irc3 event methods

    def server_ready(self, **kwargs) -> None:
        """Triggered after the server sent the MOTD (require core plugin)."""
        logger.debug(f"inside server_ready(), kwargs: {kwargs}")

        logger.info(f"Identifying with {settings.IRCBOT_NICKSERV_MASK}")
        self.bot.privmsg(
            settings.IRCBOT_NICKSERV_MASK,
            f"identify {settings.IRCBOT_NICK} {settings.IRCBOT_NICKSERV_PASSWORD}",
        )

        logger.info(
            f"Calling self.bot.do_stuff() in {settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS} seconds..",
        )
        asyncio.sleep(settings.IRCBOT_CHECK_MESSAGE_INTERVAL_SECONDS)
        self.bot.do_stuff()

    def connection_lost(self, **kwargs) -> None:
        """Triggered when connection is lost."""
        logger.debug(f"inside connection_lost(), kwargs: {kwargs}")

    def connection_made(self, **kwargs) -> None:
        """Triggered when connection is up."""
        logger.debug(f"inside connection_made(), kwargs: {kwargs}")

    ###############################################################################################
    # decorated irc3 event methods

    @irc3.event(irc3.rfc.JOIN_PART_QUIT)
    def on_join_part_quit(self, **kwargs) -> None:
        """Triggered when there is a join part or quit on a channel the bot is in."""
        logger.debug(f"inside on_join_part_quit(), kwargs: {kwargs}")

        # TODO: on part or quit check if the bot is the only remaining member of a channel,
        # if so, check if the channel should be managed, and if so, part and join the channel
        # to gain @ and register with ChanServ

    @irc3.event(irc3.rfc.JOIN)
    def on_join(self, mask, channel, **kwargs) -> None:
        """Triggered when a channel is joined by someone, including the bot itself."""
        if mask.nick == self.bot.nick:
            # the bot just joined a channel
            if (
                channel in self.get_managed_team_channels() or channel in (settings.IRCBOT_PUBLIC_CHANNEL, settings.IRCBOT_VOLUNTEER_CHANNEL)
            ):
                logger.debug(
                    f"Just joined a channel I am supposed to be managing, asking ChanServ for info about {channel}",
                )
                self.get_channel_info(channel)
                return

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_privmsg(self, **kwargs) -> None:
        """Triggered when a privmsg is sent to the bot or to a channel the bot is in."""
        # we only handle NOTICEs for now
        if kwargs["event"] != "NOTICE":
            return

        logger.debug(f"inside on_privmsg(), kwargs: {kwargs}")

        # check if this is a message from nickserv
        if kwargs["mask"] == f"NickServ!{settings.IRCBOT_NICKSERV_MASK}":
            self.bot.handle_nickserv_privmsg(**kwargs)

        # check if this is a message from chanserv
        if kwargs["mask"] == f"ChanServ!{settings.IRCBOT_CHANSERV_MASK}":
            self.bot.handle_chanserv_privmsg(**kwargs)

    @irc3.event(irc3.rfc.KICK)
    def on_kick(self, **kwargs) -> None:
        logger.debug(f"inside on_kick(), kwargs: {kwargs}")

    @irc3.event(irc3.rfc.MODE)
    def on_mode(self, **kwargs) -> None:
        """Triggered whenever a mode is changed."""
        logger.debug(f"inside on_mode(), kwargs: {kwargs}")

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
    def do_stuff(self) -> None:
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
    def get_outgoing_messages(self) -> None:
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
                logger.warning(f"skipping message to {msg.target}")

    ###############################################################################################
    # irc channel methods

    @irc3.extend
    def check_irc_channels(self) -> None:
        """Compare the list of IRC channels the bot is currently in with the list of IRC channels the bot is supposed to be in.
        Join or part channels as needed.
        """
        desired_channel_list = self.bot.get_desired_channel_list()
        # logger.debug("Inside check_irc_channels(), desired_channel_list is: %s and self.bot.channels is: %s" % (desired_channel_list, self.bot.channels.keys()))

        # loop over desired_channel_list, join as needed
        for channel in desired_channel_list:
            if channel not in self.bot.channels:
                logger.debug(
                    f"I should be in {channel} but I am not, attempting to join...",
                )
                self.bot.join(channel)

        # loop over self.bot.channels, part as needed
        for channel in self.bot.channels:
            if channel not in desired_channel_list:
                logger.debug(f"I am in {channel} but I shouldn't be, parting...")
                self.bot.part(channel, "I am no longer needed here")

    @irc3.extend
    def get_desired_channel_list(self):
        """Return a list of strings of all the IRC channels the bot is supposed to be in."""
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
    def setup_private_channel(self, channel) -> None:
        """Configures a private IRC channel by setting modes and adding all members to ACL if it is a team channel."""
        logger.debug(f"Inside setup_private_channel() for {channel}")

        # basic private channel modes
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, f"SET {channel} mlock +inpst")
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, f"SET {channel} SECURE on")
        self.bot.privmsg(
            settings.IRCBOT_CHANSERV_MASK,
            f"SET {channel} RESTRICTED on",
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
    def setup_public_channel(self, channel) -> None:
        """Configures a public IRC channel by setting modes and giving all team members +oO if it is a team channel."""
        logger.debug(f"Inside setup_public_channel() for {channel}")

        # basic private channel modes
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, f"SET {channel} mlock +nt-lk")
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, f"SET {channel} SECURE off")
        self.bot.privmsg(
            settings.IRCBOT_CHANSERV_MASK,
            f"SET {channel} RESTRICTED off",
        )

        team = get_team_from_irc_channel(channel)
        if team:
            # add members to ACL
            self.bot.add_team_members_to_channel_acl(team)
            # make sure public_irc_channel_fix_needed is set to False and save
            team.public_irc_channel_fix_needed = False
            team.save()

    @irc3.extend
    def add_team_members_to_channel_acl(self, team) -> None:
        """Handles initial ACL for team channels.
        Sets membership.irc_acl_fix_needed=True for each approved teammember with a NickServ username.
        """
        # add all members to the acl
        for membership in team.memberships.all():
            if membership.approved and membership.user.profile.nickserv_username:
                membership.irc_acl_fix_needed = True
                membership.save()

    @irc3.extend
    def add_user_to_channel_acl(self, username, channel, invite) -> None:
        """Add user to team IRC channel ACL."""
        # set autoop for this username
        self.bot.privmsg(
            settings.IRCBOT_CHANSERV_MASK,
            f"flags {channel} {username} +oO",
        )

        if invite:
            # also add autoinvite for this username
            self.bot.mode(channel, "+I", f"$a:{username}")

        # add a delay so the bot doesn't flood itself off, irc3 antiflood settings do not help here, why?
        time.sleep(1)

    @irc3.extend
    def fix_missing_acls(self) -> None:
        """Called periodically by do_stuff()
        Loops over TeamMember objects and adds ACL entries as needed
        Loops over Team objects and fixes permissions and ACLS as needed.
        """
        # first find all TeamMember objects which needs a loving hand
        missing_acls = TeamMember.objects.filter(irc_acl_fix_needed=True).exclude(
            user__profile__nickserv_username="",
        )

        # loop over them and fix what needs to be fixed
        if missing_acls:
            logger.debug(
                f"Found {missing_acls.count()} memberships which need IRC ACL fixing..",
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
                f"Team {team} private IRC channel {team.private_irc_channel_name} needs ACL fixing",
            )
            self.bot.setup_private_channel(team.private_irc_channel_name)

        # loop over teams where the public channel needs fixing
        for team in Team.objects.filter(public_irc_channel_fix_needed=True):
            logger.debug(
                f"Team {team} public IRC channel {team.public_irc_channel_name} needs ACL fixing",
            )
            self.bot.setup_public_channel(team.public_irc_channel_name)

    ###############################################################################################
    # services (ChanServ & NickServ) methods

    @irc3.extend
    def handle_chanserv_privmsg(self, **kwargs) -> None:
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
                        f"ChanServ says channel {channel} is not registered, bot is supposed to be managing this channel, registering it with chanserv",
                    )
                    self.bot.privmsg(
                        settings.IRCBOT_CHANSERV_MASK,
                        f"register {channel}",
                    )
                else:
                    logger.debug(
                        f"ChanServ says channel {channel} is not registered, bot is supposed to be managing this channel, but the bot cannot register without @ in the channel",
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
                f"Channel {channel} was registered with ChanServ, looking up Team...",
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
            logger.debug(f"Unable to find Team matching IRC channel {channel}")

            # check if this channel is the volunteer channel
            if channel == settings.IRCBOT_VOLUNTEER_CHANNEL:
                logger.debug(f"{channel} is the volunteer channel, setting up")
                self.bot.setup_private_channel(channel)
                # lets handle the volunteer channels initial ACL manually..
                return

        logger.debug("Unhandled ChanServ message: {}".format(kwargs["data"]))

    @irc3.extend
    def handle_nickserv_privmsg(self, **kwargs) -> None:
        """Handles messages from NickServ on networks with Services."""
        logger.debug("Got a message from NickServ")

        # handle "\x02botnick\x02 is not a registered nickname." message
        if kwargs["data"] == f"\x02{self.bot.nick}\x02 is not a registered nickname.":
            # the bots nickname is not registered, register new account with nickserv
            self.bot.privmsg(
                settings.IRCBOT_NICKSERV_MASK,
                f"register {settings.IRCBOT_NICKSERV_PASSWORD} {settings.IRCBOT_NICKSERV_EMAIL}",
            )
            return

        logger.debug("Unhandled NickServ message: {}".format(kwargs["data"]))

    @irc3.extend
    def get_channel_info(self, channel) -> None:
        """Ask ChanServ for info about a channel."""
        self.bot.privmsg(settings.IRCBOT_CHANSERV_MASK, f"info {channel}")
