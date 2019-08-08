from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.conf import settings
from django.template.loader import render_to_string
from .models import OutgoingEmail
import logging, magic

logger = logging.getLogger("bornhack.%s" % __name__)


def _send_email(
    text_template,
    subject,
    to_recipients=[],
    cc_recipients=[],
    bcc_recipients=[],
    html_template="",
    sender="BornHack <info@bornhack.dk>",
    attachment=None,
    attachment_filename="",
):
    if not isinstance(to_recipients, list):
        to_recipients = [to_recipients]

    try:
        # put the basic email together
        msg = EmailMultiAlternatives(
            subject,
            text_template,
            sender,
            to_recipients,
            bcc_recipients + [settings.ARCHIVE_EMAIL]
            if bcc_recipients
            else [settings.ARCHIVE_EMAIL],
            cc_recipients,
        )

        # is there a html version of this email?
        if html_template:
            msg.attach_alternative(html_template, "text/html")

        # is there an attachment to this mail?
        if attachment
            # figure out the mimetype
            mimetype = magic.from_buffer(attachment, mime=True)
            msg.attach(attachment_filename, attachment, mimetype)
    except Exception as e:
        logger.exception("exception while rendering email: {}".format(e))
        return False

    # send the email
    try:
        msg.send(fail_silently=False)
    except Exception as e:
        logger.exception("exception while sending email: {}".format(e))
        return False

    return True


def add_outgoing_email(
    text_template,
    formatdict,
    subject,
    to_recipients=[],
    cc_recipients=[],
    bcc_recipients=[],
    html_template="",
    sender="BornHack <info@bornhack.dk>",
    attachment=None,
    attachment_filename="",
    attachments=None,
):
    """ adds an email to the outgoing queue
        recipients is a list of to recipients
    """
    text_template = render_to_string(text_template, formatdict)

    if html_template:
        html_template = render_to_string(html_template, formatdict)

    if not isinstance(to_recipients, list):
        to_recipients = [to_recipients]

    for recipient in to_recipients:
        try:
            validate_email(recipient)
        except ValidationError:
            return False

    email = OutgoingEmail.objects.create(
        text_template=text_template,
        html_template=html_template,
        subject=subject,
        sender=sender,
        to_recipients=to_recipients,
        cc_recipients=cc_recipients,
        bcc_recipients=bcc_recipients,
    )

    return True
