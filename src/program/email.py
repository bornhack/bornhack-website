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
