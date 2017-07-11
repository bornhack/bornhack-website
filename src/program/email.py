from django.core.exceptions import ObjectDoesNotExist

from utils.email import add_outgoing_email
from teams.models import Team
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def add_new_speakerproposal_email(speakerproposal):
    formatdict = {
        'proposal': speakerproposal
    }

    try:
        content_team = Team.objects.get(
            camp=speakerproposal.camp, name='Content'
        )

        return add_outgoing_email(
            text_template='emails/new_speakerproposal.txt',
            html_template='emails/new_speakerproposal.html',
            to_recipients=content_team.mailing_list,
            formatdict=formatdict,
            subject='New speaker proposal for {}'.format(
                speakerproposal.camp.title
            )
        )
    except ObjectDoesNotExist as e:
        logger.info('There is no team with name Content: {}'.format(e))
        return False


def add_new_eventproposal_email(eventproposal):
    formatdict = {
        'proposal': eventproposal
    }

    try:
        content_team = Team.objects.get(
            camp=eventproposal.camp, name='Content'
        )

        return add_outgoing_email(
            text_template='emails/new_eventproposal.txt',
            html_template='emails/new_eventproposal.html',
            to_recipients=content_team.mailing_list,
            formatdict=formatdict,
            subject='New event proposal for {}'.format(
                eventproposal.camp.title
            )
        )
    except ObjectDoesNotExist as e:
        logger.info('There is no team with name Content: {}'.format(e))
        return False


def add_speakerproposal_updated_email(speakerproposal):
    formatdict = {
        'proposal': speakerproposal
    }

    try:
        content_team = Team.objects.get(
            camp=speakerproposal.camp, name='Content'
        )

        return add_outgoing_email(
            text_template='emails/update_speakerproposal.txt',
            html_template='emails/update_speakerproposal.html',
            to_recipients=content_team.mailing_list,
            formatdict=formatdict,
            subject='Updated speaker proposal for {}'.format(
                speakerproposal.camp.title
            )
        )
    except ObjectDoesNotExist as e:
        logger.info('There is no team with name Content: {}'.format(e))
        return False


def add_eventproposal_updated_email(eventproposal):
    formatdict = {
        'proposal': eventproposal
    }

    try:
        content_team = Team.objects.get(
            camp=eventproposal.camp, name='Content'
        )

        return add_outgoing_email(
            text_template='emails/update_eventproposal.txt',
            html_template='emails/update_eventproposal.html',
            to_recipients=content_team.mailing_list,
            formatdict=formatdict,
            subject='New event proposal for {}'.format(
                eventproposal.camp.title
            )
        )
    except ObjectDoesNotExist as e:
        logger.info('There is no team with name Content: {}'.format(e))
        return False
