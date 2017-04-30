from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.core.files.base import ContentFile
from django.conf import settings
from django.template.loader import render_to_string
from .models import OutgoingEmail
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def _send_email(
    text_template,
    recipient,
    subject,
    html_template='',
    sender='BornHack <info@bornhack.dk>',
    attachment=None,
    attachment_filename=''
):
    if not isinstance(recipient, list):
        recipient = [recipient]

    try:
        # put the basic email together
        msg = EmailMultiAlternatives(
            subject,
            text_template,
            sender,
            recipient,
            [settings.ARCHIVE_EMAIL]
        )

        # is there a html version of this email?
        if html_template:
            msg.attach_alternative(
                html_template,
                'text/html'
            )

        # is there a pdf attachment to this mail?
        if attachment:
            msg.attach(attachment_filename, attachment, 'application/pdf')
    except Exception as e:
        logger.exception('exception while rendering email: {}'.format(e))
        return False

    # send the email
    try:
        msg.send(fail_silently=False)
    except Exception as e:
        logger.exception('exception while sending email: {}'.format(e))
        return False

    return True


def add_outgoing_email(
    text_template,
    recipients,
    formatdict,
    subject,
    html_template='',
    sender='BornHack <info@bornhack.dk>',
    attachment=None,
    attachment_filename=''
):
    """ adds an email to the outgoing queue
        recipients is either just a str email or a str commaseperated emails
    """
    text_template = render_to_string(text_template, formatdict)

    if html_template:
        html_template = render_to_string(html_template, formatdict)

    if ',' in recipients:
        for recipient in recipients.split(','):
            validate_email(recipient.strip())
    else:
        validate_email(recipients)

    email = OutgoingEmail.objects.create(
        text_template=text_template,
        html_template=html_template,
        subject=subject,
        sender=sender,
        recipient=recipients
    )

    if attachment:
        django_file = ContentFile(attachment)
        django_file.name = attachment_filename
        email.attachment.save(attachment_filename, django_file, save=True)

    return True
