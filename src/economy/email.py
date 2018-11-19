import os

from django.conf import settings

from utils.email import add_outgoing_email

# expense emails

def send_accountingsystem_expense_email(expense):
    """
    Sends an email to the accountingsystem with the invoice as an attachment,
    and with the expense uuid and description in email subject
    """
    add_outgoing_email(
        "emails/accountingsystem_expense_email.txt",
        formatdict=dict(expense=expense),
        subject="Expense %s for %s" % (expense.pk, expense.camp.title),
        to_recipients=[settings.ACCOUNTINGSYSTEM_EMAIL],
        attachment=expense.invoice.read(),
        attachment_filename=os.path.basename(expense.invoice.file.name),
    )


def send_expense_approved_email(expense):
    """
    Sends an expense-approved email to the user who created the expense
    """
    add_outgoing_email(
        "emails/expense_approved_email.txt",
        formatdict=dict(expense=expense),
        subject="Your expense for %s has been approved." % expense.camp.title,
        to_recipients=[expense.user.emailaddress_set.get(primary=True).email],
    )


def send_expense_rejected_email(expense):
    """
    Sends an expense-rejected email to the user who created the expense
    """
    add_outgoing_email(
        "emails/expense_rejected_email.txt",
        formatdict=dict(expense=expense),
        subject="Your expense for %s has been rejected." % expense.camp.title,
        to_recipients=[expense.user.emailaddress_set.get(primary=True).email],
    )

# revenue emails

def send_accountingsystem_revenue_email(revenue):
    """
    Sends an email to the accountingsystem with the invoice as an attachment,
    and with the revenue uuid and description in email subject
    """
    add_outgoing_email(
        "emails/accountingsystem_revenue_email.txt",
        formatdict=dict(revenue=revenue),
        subject="Revenue %s for %s" % (revenue.pk, revenue.camp.title),
        to_recipients=[settings.ACCOUNTINGSYSTEM_EMAIL],
        attachment=revenue.invoice.read(),
        attachment_filename=os.path.basename(revenue.invoice.file.name),
    )


def send_revenue_approved_email(revenue):
    """
    Sends a revenue-approved email to the user who created the revenue
    """
    add_outgoing_email(
        "emails/revenue_approved_email.txt",
        formatdict=dict(revenue=revenue),
        subject="Your revenue for %s has been approved." % revenue.camp.title,
        to_recipients=[revenue.user.emailaddress_set.get(primary=True).email],
    )


def send_revenue_rejected_email(revenue):
    """
    Sends an revenue-rejected email to the user who created the revenue
    """
    add_outgoing_email(
        "emails/revenue_rejected_email.txt",
        formatdict=dict(revenue=revenue),
        subject="Your revenue for %s has been rejected." % revenue.camp.title,
        to_recipients=[revenue.user.emailaddress_set.get(primary=True).email],
    )

