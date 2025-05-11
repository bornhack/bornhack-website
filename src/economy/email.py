from __future__ import annotations

import os

from django.conf import settings

from teams.models import Team
from utils.email import add_outgoing_email

# expense emails


def send_accountingsystem_expense_email(expense):
    """Sends an email to the accountingsystem with the invoice as an attachment,
    and with the expense uuid and description in email subject
    """
    economy_team = Team.objects.get(camp=expense.camp, name=settings.ECONOMY_TEAM_NAME)
    add_outgoing_email(
        responsible_team=economy_team,
        text_template="emails/accountingsystem_expense_email.txt",
        formatdict={"expense": expense},
        subject=f"Expense {expense.pk} for {expense.camp.title}",
        to_recipients=[settings.ACCOUNTINGSYSTEM_EMAIL],
        attachment=expense.invoice.read(),
        attachment_filename=os.path.basename(expense.invoice.file.name),
    )


def send_expense_approved_email(expense):
    """Sends an expense-approved email to the user who created the expense"""
    economy_team = Team.objects.get(camp=expense.camp, name=settings.ECONOMY_TEAM_NAME)
    add_outgoing_email(
        responsible_team=economy_team,
        text_template="emails/expense_approved_email.txt",
        formatdict={"expense": expense},
        subject="Your expense for %s has been approved." % expense.camp.title,
        to_recipients=[expense.user.emailaddress_set.get(primary=True).email],
    )


def send_expense_rejected_email(expense):
    """Sends an expense-rejected email to the user who created the expense"""
    economy_team = Team.objects.get(camp=expense.camp, name=settings.ECONOMY_TEAM_NAME)
    add_outgoing_email(
        responsible_team=economy_team,
        text_template="emails/expense_rejected_email.txt",
        formatdict={"expense": expense},
        subject="Your expense for %s has been rejected." % expense.camp.title,
        to_recipients=[expense.user.emailaddress_set.get(primary=True).email],
    )


# revenue emails


def send_accountingsystem_revenue_email(revenue):
    """Sends an email to the accountingsystem with the invoice as an attachment,
    and with the revenue uuid and description in email subject
    """
    economy_team = Team.objects.get(camp=revenue.camp, name=settings.ECONOMY_TEAM_NAME)
    add_outgoing_email(
        responsible_team=economy_team,
        text_template="emails/accountingsystem_revenue_email.txt",
        formatdict={"revenue": revenue},
        subject=f"Revenue {revenue.pk} for {revenue.camp.title}",
        to_recipients=[settings.ACCOUNTINGSYSTEM_EMAIL],
        attachment=revenue.invoice.read(),
        attachment_filename=os.path.basename(revenue.invoice.file.name),
    )


def send_revenue_approved_email(revenue):
    """Sends a revenue-approved email to the user who created the revenue"""
    economy_team = Team.objects.get(camp=revenue.camp, name=settings.ECONOMY_TEAM_NAME)
    add_outgoing_email(
        responsible_team=economy_team,
        text_template="emails/revenue_approved_email.txt",
        formatdict={"revenue": revenue},
        subject="Your revenue for %s has been approved." % revenue.camp.title,
        to_recipients=[revenue.user.emailaddress_set.get(primary=True).email],
    )


def send_revenue_rejected_email(revenue):
    """Sends an revenue-rejected email to the user who created the revenue"""
    economy_team = Team.objects.get(camp=revenue.camp, name=settings.ECONOMY_TEAM_NAME)
    add_outgoing_email(
        responsible_team=economy_team,
        text_template="emails/revenue_rejected_email.txt",
        formatdict={"revenue": revenue},
        subject="Your revenue for %s has been rejected." % revenue.camp.title,
        to_recipients=[revenue.user.emailaddress_set.get(primary=True).email],
    )
