from utils.email import add_outgoing_email
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def add_creditnote_email(creditnote):
    # put formatdict together
    formatdict = {
        'creditnote': creditnote,
    }

    subject = 'BornHack creditnote %s' % creditnote.pk

    # add email to outgoing email queue
    return add_outgoing_email(
        text_template='emails/creditnote_email.txt',
        html_template='emails/creditnote_email.html',
        to_recipients=creditnote.user.email,
        formatdict=formatdict,
        subject=subject,
        attachment=creditnote.pdf.read(),
        attachment_filename=creditnote.filename
    )


def add_invoice_email(invoice):
    # put formatdict together
    formatdict = {
        'ordernumber': invoice.order.pk,
        'invoicenumber': invoice.pk,
        'filename': invoice.filename,
    }

    subject = 'BornHack invoice %s' % invoice.pk

    # add email to outgoing email queue
    return add_outgoing_email(
        text_template='emails/invoice_email.txt',
        html_template='emails/invoice_email.html',
        to_recipients=invoice.order.user.email,
        formatdict=formatdict,
        subject=subject,
        attachment=invoice.pdf.read(),
        attachment_filename=invoice.filename
    )


def add_test_email(recipient):
    return add_outgoing_email(
        text_template='emails/testmail.txt',
        to_recipients=recipient,
        subject='testmail from bornhack website'
    )
