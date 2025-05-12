from __future__ import annotations

import logging

from ircbot.utils import add_irc_message

logger = logging.getLogger(f"bornhack.{__name__}")


def handle_team_event(
    eventtype,
    irc_message=None,
    irc_timeout=60,
    email_template=None,
    email_formatdict=None,
) -> None:
    """This method is our basic event handler.
    The type of event determines which teams receive notifications.
    TODO: Add some sort of priority to messages.
    """
    # logger.info("Inside handle_team_event, eventtype %s" % eventtype)

    # get event type from database
    from .models import Type

    try:
        eventtype = Type.objects.get(name=eventtype)
    except Type.DoesNotExist:
        # unknown event type, do nothing
        logger.exception(f"Unknown eventtype {eventtype}")
        return

    if not eventtype.teams:
        # no routes found for this eventtype, do nothing
        # logger.error("No routes round for eventtype %s" % eventtype)
        return

    # loop over routes (teams) for this eventtype
    for team in eventtype.teams:
        logger.debug(f"Handling eventtype {eventtype} for team {team}")
        team_irc_notification(
            team=team,
            eventtype=eventtype,
            irc_message=irc_message,
            irc_timeout=irc_timeout,
        )
        team_email_notification(
            team=team,
            eventtype=eventtype,
            email_template=None,
            email_formatdict=None,
        )
        # handle any future notification types here..


def team_irc_notification(team, eventtype, irc_message=None, irc_timeout=60) -> None:
    """Sends IRC notifications for events to team IRC channels."""
    logger.debug(f"Inside team_irc_notification, message {irc_message}")
    if not irc_message:
        logger.error("No IRC message found")
        return

    if not eventtype.irc_notification:
        logger.error(f"IRC notifications not enabled for eventtype {eventtype}")
        return

    if not team.private_irc_channel_name or not team.private_irc_channel_bot:
        logger.error(
            f"team {team} does not have a private IRC channel, or does not have the bot in the channel",
        )
        return

    # send an IRC message to the the channel for this team
    add_irc_message(
        target=team.private_irc_channel_name,
        message=irc_message,
        timeout=60,
    )
    logger.debug(f"Added new IRC message for channel {team.private_irc_channel_name}")


def team_email_notification(
    team,
    eventtype,
    email_template=None,
    email_formatdict=None,
) -> None:
    """Sends email notifications for events to team mailinglists (if possible,
    otherwise directly to the team leads).
    """
    if not email_template or not email_formatdict or not eventtype.email_notification:
        # no email message found, or email notifications are not enabled for this event type
        return

    if team.mailing_list:
        # send notification to the team mailing list
        recipient_list = [team.mailing_list]
    else:
        # no team mailinglist, send to the team leads instead
        recipient_list = [resp.email for resp in team.leads.all()]

    # TODO: actually send the email here
    logger.debug(f"sending test email to {recipient_list}")
