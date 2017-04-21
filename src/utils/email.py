from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def _send_email(
    text_template,
    recipient,
    formatdict,
    subject,
    html_template=None,
    sender='BornHack <info@bornhack.dk>',
    attachment=None,
    attachment_filename=None
):
    if not isinstance(recipient, list):
        recipient = [recipient]

    try:
        # put the basic email together
        msg = EmailMultiAlternatives(
            subject,
            render_to_string(text_template, formatdict),
            sender,
            recipient,
            [settings.ARCHIVE_EMAIL]
        )

        # is there a html version of this email?
        if html_template:
            msg.attach_alternative(
                render_to_string(html_template, formatdict),
                'text/html'
            )

        # is there a pdf attachment to this mail?
        if attachment:
            msg.attach(attachment_filename, attachment, 'application/pdf')

    except Exception as e:
        logger.exception('exception while rendering email: {}'.format(e))
        return False

    # send the email
    msg.send()

    return True
