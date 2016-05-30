from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string


def send_email(emailtype, recipient, formatdict, subject, sender='BornHack <info@bornhack.dk>', attachment=None):
    ### determine email type, set template and attachment vars
    html_template=None

    if emailtype == 'invoice':
        text_template = 'emails/invoice_email.txt'
        html_template = 'emails/invoice_email.html'
        attachment_filename = formatdict['filename']
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

        ### is there a pdf attachment to this mail?
        if attachment:
            msg.attach(attachment_filename, attachment, 'application/pdf')

    except Exception as E:
        print 'exception while rendering email: %s' % E
        return False
    
    ### send the email
    msg.send()

    ### all good
    return True


def send_invoice_email(invoice):
    # put formatdict together
    formatdict = {
        'ordernumber': invoice.order.pk,
        'invoicenumber': invoice.pk,
        'filename': invoice.filename,
    }

    subject = 'BornHack invoice %s' % invoice.pk

    # send mail
    return send_email(
        emailtype='invoice',
        recipient=invoice.order.user.email,
        formatdict=formatdict,
        subject=subject,
        sender='info@bornhack.dk',
        attachment=invoice.pdf.read(),
    )


def send_test_email(recipient):
    return send_email(
        emailtype='testmail',
        recipient=recipient,
        subject='testmail from bornhack website',
    )

