from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string


def send_email(emailtype, recipient, formatdict, subject, sender='BornHack <noreply@bornhack.dk>', attachment=None):
    ### determine email type, set template and attachment vars
    html_template=None

    if emailtype == 'invoice':
        text_template = 'emails/invoice.txt'
        html_template = 'emails/invoice.html'
        attachment_filename = formatdict['attachmentname']
    elif emailtype == 'testmail':
        text_template = 'emails/testmail.txt'
    else:
        print 'Unknown email type: %s' % emailtype
        return False

    try:
        ### put the basic email together
        msg = EmailMultiAlternatives(subject, render_to_string(text_template, formatdict), sender, [recipient], [settings.ARCHIVE_EMAIL])
        
        ### is there a html version of this email?
        if html_template:
            msg.attach_alternative(render_to_string(html_template, formatdict), 'text/html')

        ### is there an attachment to this mail?
        if attachment:
            msg.attach(attachment_filename, attachment, 'application/pdf')

    except Exception as E:
        print 'exception while rendering email: %s' % E
        return False
    
    ### send the email
    msg.send()

    ### all good
    return True


def send_invoice_email(invoice, attachment):
    # put formatdict together
    formatdict = {
        'order': invoice.order,
        'attachmentname': invoice.filename,
    }

    subject = 'BornHack invoice %s' % order.pk

    # send mail
    return send_email(
        emailtype='invoice',
        recipient=order.user.email,
        formatdict=formatdict,
        subject=subject,
        sender='noreply@bornfiber.dk',
    )


def send_test_email(recipient):
    return send_email(
        emailtype='testmail',
        recipient=recipient,
        subject='testmail from bornhack website',
    )

