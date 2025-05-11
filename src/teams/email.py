import logging

from utils.email import add_outgoing_email

logger = logging.getLogger("bornhack.%s" % __name__)


def add_added_membership_email(membership):
    formatdict = {"team": membership.team.name, "camp": membership.team.camp.title}

    return add_outgoing_email(
        responsible_team=membership.team,
        text_template="emails/add_membership_email.txt",
        html_template="emails/add_membership_email.html",
        to_recipients=membership.user.email,
        formatdict=formatdict,
        subject=f"Team update from {membership.team.camp.title}",
        hold=False,
    )


def add_removed_membership_email(membership):
    formatdict = {"team": membership.team.name, "camp": membership.team.camp.title}

    if membership.approved:
        text_template = ("emails/remove_membership_email.txt",)
        html_template = "emails/remove_membership_email.html"
    else:
        text_template = ("emails/unapproved_membership_email.txt",)
        html_template = "emails/unapproved_membership_email.html"

    return add_outgoing_email(
        responsible_team=membership.team,
        text_template=text_template,
        html_template=html_template,
        to_recipients=membership.user.email,
        formatdict=formatdict,
        subject=f"Team update from {membership.team.camp.title}",
        hold=True,
    )


def add_new_membership_email(membership):
    formatdict = {
        "team": membership.team.name,
        "camp": membership.team.camp.title,
        "memberlist_link": f"https://bornhack.dk/{membership.team.camp.slug}/teams/{membership.team.slug}/members",
    }

    return add_outgoing_email(
        responsible_team=membership.team,
        text_template="emails/new_membership_email.txt",
        html_template="emails/new_membership_email.html",
        to_recipients=[resp.email for resp in membership.team.leads.all()],
        formatdict=formatdict,
        subject=f"New membership request for {membership.team.name} at {membership.team.camp.title}",
        hold=False,
    )
