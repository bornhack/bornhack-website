from __future__ import annotations

import logging

from .email import _send_email
from .models import OutgoingEmail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bornhack.%s" % __name__)


def do_work():
    """The outgoing email worker sends emails added to the OutgoingEmail
    queue.
    """
    not_processed_email = OutgoingEmail.objects.filter(processed=False, hold=False)

    if len(not_processed_email) > 0:
        logger.debug(f"about to process {len(not_processed_email)} emails")

    for email in not_processed_email:
        attachment = None
        attachment_filename = ""
        if email.attachment:
            attachment = email.attachment.read()
            attachment_filename = email.attachment.name

        mail_send_success = _send_email(
            text_template=email.text_template,
            to_recipients=email.to_recipients,
            subject=email.subject,
            cc_recipients=email.cc_recipients,
            bcc_recipients=email.bcc_recipients,
            html_template=email.html_template,
            attachment=attachment,
            attachment_filename=attachment_filename,
        )
        if mail_send_success:
            email.processed = True
            email.save()
            logger.debug(f"Successfully sent {email}")
        else:
            logger.error(f"Unable to send {email}")
