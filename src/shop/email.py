from utils.email import _send_email
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def send_creditnote_email(creditnote):
    # put formatdict together
    formatdict = {
        'creditnote': creditnote,
    }

    subject = 'BornHack creditnote %s' % creditnote.pk

    # send mail
    return _send_email(
        text_template='emails/creditnote_email.txt',
        html_template='emails/creditnote_email.html',
        recipient=creditnote.user.email,
        formatdict=formatdict,
        subject=subject,
        attachment=creditnote.pdf.read(),
        attachment_filename=creditnote.filename
    )


def send_invoice_email(invoice):
    # put formatdict together
    formatdict = {
        'ordernumber': invoice.order.pk,
        'invoicenumber': invoice.pk,
        'filename': invoice.filename,
    }

    subject = 'BornHack invoice %s' % invoice.pk

    # send mail
    return _send_email(
        text_template='emails/invoice_email.txt',
        html_template='emails/invoice_email.html',
        recipient=invoice.order.user.email,
        formatdict=formatdict,
        subject=subject,
        attachment=invoice.pdf.read(),
        attachment_filename=invoice.filename
    )


def send_test_email(recipient):
    return _send_email(
        text_template='emails/testmail.txt',
        recipient=recipient,
        subject='testmail from bornhack website'
    )
