import logging

from django.core.exceptions import ObjectDoesNotExist
from teams.models import Team
from utils.email import add_outgoing_email

logger = logging.getLogger("bornhack.%s" % __name__)


def add_new_speakerproposal_email(speakerproposal):
    formatdict = {"proposal": speakerproposal}

    try:
        content_team = Team.objects.get(camp=speakerproposal.camp, name="Content")
    except ObjectDoesNotExist as e:
        logger.info("There is no team with name Content: {}".format(e))
        return False

    return add_outgoing_email(
        text_template="emails/new_speakerproposal.txt",
        html_template="emails/new_speakerproposal.html",
        to_recipients=content_team.mailing_list,
        formatdict=formatdict,
        subject="New speaker proposal '%s' was just submitted" % speakerproposal.name,
    )


def add_new_eventproposal_email(eventproposal):
    formatdict = {"proposal": eventproposal}

    try:
        content_team = Team.objects.get(camp=eventproposal.camp, name="Content")
    except ObjectDoesNotExist as e:
        logger.info("There is no team with name Content: {}".format(e))
        return False

    return add_outgoing_email(
        text_template="emails/new_eventproposal.txt",
        html_template="emails/new_eventproposal.html",
        to_recipients=content_team.mailing_list,
        formatdict=formatdict,
        subject="New event proposal '%s' was just submitted" % eventproposal.title,
    )


def add_speakerproposal_updated_email(speakerproposal):
    formatdict = {"proposal": speakerproposal}

    try:
        content_team = Team.objects.get(camp=speakerproposal.camp, name="Content")
    except ObjectDoesNotExist as e:
        logger.info("There is no team with name Content: {}".format(e))
        return False

    return add_outgoing_email(
        text_template="emails/update_speakerproposal.txt",
        html_template="emails/update_speakerproposal.html",
        to_recipients=content_team.mailing_list,
        formatdict=formatdict,
        subject="Speaker proposal '%s' was just updated" % speakerproposal.name,
    )


def add_eventproposal_updated_email(eventproposal):
    formatdict = {"proposal": eventproposal}

    try:
        content_team = Team.objects.get(camp=eventproposal.camp, name="Content")
    except ObjectDoesNotExist as e:
        logger.info("There is no team with name Content: {}".format(e))
        return False

    return add_outgoing_email(
        text_template="emails/update_eventproposal.txt",
        html_template="emails/update_eventproposal.html",
        to_recipients=content_team.mailing_list,
        formatdict=formatdict,
        subject="Event proposal '%s' was just updated" % eventproposal.title,
    )


def add_speakerproposal_rejected_email(speakerproposal):
    formatdict = {"proposal": speakerproposal}

    return add_outgoing_email(
        text_template="emails/speakerproposal_rejected.txt",
        html_template="emails/speakerproposal_rejected.html",
        to_recipients=speakerproposal.user.email,
        formatdict=formatdict,
        subject=f"Your {speakerproposal.camp.title} speaker proposal '{speakerproposal.name}' was rejected",
    )


def add_speakerproposal_accepted_email(speakerproposal):
    formatdict = {"proposal": speakerproposal}

    return add_outgoing_email(
        text_template="emails/speakerproposal_accepted.txt",
        html_template="emails/speakerproposal_accepted.html",
        to_recipients=speakerproposal.user.email,
        formatdict=formatdict,
        subject=f"Your {speakerproposal.camp.title} speaker proposal '{speakerproposal.name}' was accepted",
    )


def add_eventproposal_rejected_email(eventproposal):
    formatdict = {"proposal": eventproposal}

    return add_outgoing_email(
        text_template="emails/eventproposal_rejected.txt",
        html_template="emails/eventproposal_rejected.html",
        to_recipients=eventproposal.user.email,
        formatdict=formatdict,
        subject=f"Your {eventproposal.camp.title} event proposal '{eventproposal.title}' was rejected",
    )


def add_eventproposal_accepted_email(eventproposal):
    formatdict = {"proposal": eventproposal}

    return add_outgoing_email(
        text_template="emails/eventproposal_accepted.txt",
        html_template="emails/eventproposal_accepted.html",
        to_recipients=eventproposal.user.email,
        formatdict=formatdict,
        subject=f"Your {eventproposal.camp.title} event proposal '{eventproposal.title}' was accepted!",
    )


def add_event_scheduled_email(eventinstance, action):
    formatdict = {"eventinstance": eventinstance, "action": action}
    recipients = [speaker.email for speaker in eventinstance.event.speakers.all()]
    recipients.append(eventinstance.event.proposal.user.email)
    # loop over unique recipients and send an email to each
    for rcpt in set(recipients):
        return add_outgoing_email(
            text_template="emails/event_scheduled.txt",
            html_template="emails/event_scheduled.html",
            to_recipients=rcpt,
            formatdict=formatdict,
            subject=f"Your {eventinstance.camp.title} event '{eventinstance.event.title}' has been {action}!",
        )
