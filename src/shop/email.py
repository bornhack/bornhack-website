import logging

from django.conf import settings

from utils.email import add_outgoing_email

logger = logging.getLogger("bornhack.%s" % __name__)


def add_creditnote_email(creditnote):
    # put formatdict together
    formatdict = {"creditnote": creditnote}

    subject = "BornHack creditnote %s" % creditnote.pk

    # add email to outgoing email queue
    return add_outgoing_email(
        text_template="emails/creditnote_email.txt",
        html_template="emails/creditnote_email.html",
        to_recipients=creditnote.user.email,
        bcc_recipients=settings.ACCOUNTINGSYSTEM_EMAIL,
        formatdict=formatdict,
        subject=subject,
        attachment=creditnote.pdf.read(),
        attachment_filename=creditnote.filename,
    )


def add_invoice_email(invoice):
    # put formatdict together
    formatdict = {
        "ordernumber": invoice.order.pk,
        "invoicenumber": invoice.pk,
        "filename": invoice.filename,
    }

    subject = "BornHack invoice %s" % invoice.pk

    # add email to outgoing email queue
    return add_outgoing_email(
        text_template="emails/invoice_email.txt",
        html_template="emails/invoice_email.html",
        to_recipients=invoice.order.user.email,
        bcc_recipients=settings.ACCOUNTINGSYSTEM_EMAIL,
        formatdict=formatdict,
        subject=subject,
        attachment=invoice.pdf.read(),
        attachment_filename=invoice.filename,
    )
