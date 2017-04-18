from utils.email import _send_email
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def send_add_membership_email(membership):
    formatdict = {
        'team': membership.team.name,
        'camp': membership.team.camp.title
    }

    return _send_email(
        text_template='emails/add_membership_email.txt',
        html_template='emails/add_membership_email.html',
        recipient=membership.user.email,
        formatdict=formatdict,
        subject='Team update from {}'.format(membership.team.camp.title)
    )


def send_remove_membership_email(membership):
    formatdict = {
        'team': membership.team.name,
        'camp': membership.team.camp.title
    }

    if membership.approved:
        text_template = 'emails/remove_membership_email.txt',
        html_template = 'emails/remove_membership_email.html'
    else:
        text_template = 'emails/unapproved_membership_email.txt',
        html_template = 'emails/unapproved_membership_email.html'

    return _send_email(
        text_template=text_template,
        html_template=html_template,
        recipient=membership.user.email,
        formatdict=formatdict,
        subject='Team update from {}'.format(membership.team.camp.title)
    )


def send_new_membership_email(membership):
    formatdict = {
        'team': membership.team.name,
        'camp': membership.team.camp.title
    }

    return _send_email(
        text_template='emails/new_membership_email.txt',
        html_template='emails/new_membership_email.html',
        recipient=membership.user.email,
        formatdict=formatdict,
        subject='New membership request for {} at {}'.format(
            membership.team.name,
            membership.team.camp.title
        )
    )
