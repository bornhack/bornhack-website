import os

from django.conf import settings

from utils.email import add_outgoing_email


def send_accountingsystem_email(expense):
    """
    Sends an email to the accountingsystem with the invoice as an attachment,
    and with the expense uuid and description in email subject
    """
    add_outgoing_email(
        "emails/accountingsystem_email.txt",
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

