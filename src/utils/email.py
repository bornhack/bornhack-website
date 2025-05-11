import logging

import magic
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.template.loader import render_to_string

from .models import OutgoingEmail

logger = logging.getLogger("bornhack.%s" % __name__)


def _send_email(
    text_template,
    subject,
    to_recipients=None,
    cc_recipients=None,
    bcc_recipients=None,
    html_template="",
    sender="BornHack <info@bornhack.dk>",
    attachment=None,
    attachment_filename="",
):
    to_recipients = to_recipients or []
    cc_recipients = cc_recipients or []
    bcc_recipients = bcc_recipients or []

    if not isinstance(to_recipients, list):
        to_recipients = [to_recipients]

    if not isinstance(cc_recipients, list):
        cc_recipients = [cc_recipients]

    if not isinstance(bcc_recipients, list):
        bcc_recipients = [bcc_recipients]

    try:
        # put the basic email together
        msg = EmailMultiAlternatives(
            subject,
            text_template,
            sender,
            to_recipients,
            (bcc_recipients + [settings.ARCHIVE_EMAIL] if bcc_recipients else [settings.ARCHIVE_EMAIL]),
            cc_recipients,
        )

        # is there a html version of this email?
        if html_template:
            msg.attach_alternative(html_template, "text/html")

        # is there an attachment to this mail?
        if attachment:
            # figure out the mimetype
            mimetype = magic.from_buffer(attachment, mime=True)
            msg.attach(attachment_filename, attachment, mimetype)
    except Exception as e:
        logger.exception(f"exception while rendering email: {e}")
        return False

    # send the email
    try:
        msg.send(fail_silently=False)
    except Exception as e:
        logger.exception(f"exception while sending email: {e}")
        return False

    return True


def add_outgoing_email(
    text_template,
    formatdict,
    subject,
    to_recipients=None,
    cc_recipients=None,
    bcc_recipients=None,
    html_template="",
    sender="BornHack <info@bornhack.dk>",
    attachment=None,
    attachment_filename="",
    responsible_team=None,
    hold=False,
):
    """Adds an email to the outgoing queue
    recipients is a list of to recipients
    """
    to_recipients = to_recipients or []
    cc_recipients = cc_recipients or []
    bcc_recipients = bcc_recipients or []

    text_template = render_to_string(text_template, formatdict)

    if html_template:
        html_template = render_to_string(html_template, formatdict)

    if not isinstance(to_recipients, list):
        to_recipients = [to_recipients]

    if not isinstance(cc_recipients, list):
        cc_recipients = [cc_recipients]

    if not isinstance(bcc_recipients, list):
        bcc_recipients = [bcc_recipients]

    # loop over recipients and validate each
    for recipient in to_recipients + cc_recipients + bcc_recipients:
        try:
            validate_email(recipient)
        except ValidationError:
            logger.error(
                f"There was a problem validating the email {recipient} - returning False",
            )
            return False

    email = OutgoingEmail.objects.create(
        text_template=text_template,
        html_template=html_template,
        subject=subject,
        sender=sender,
        to_recipients=to_recipients,
        cc_recipients=cc_recipients,
        bcc_recipients=bcc_recipients,
        hold=hold,
        responsible_team=responsible_team,
    )

    if attachment:
        django_file = ContentFile(attachment)
        django_file.name = attachment_filename
        email.attachment.save(attachment_filename, django_file, save=True)

    return True
