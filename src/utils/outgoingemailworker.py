from .models import OutgoingEmail
from .email import _send_email
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bornhack.%s' % __name__)


def do_work():
    """
        The outgoing email worker sends emails added to the OutgoingEmail
        queue.
    """
    not_processed_email = OutgoingEmail.objects.filter(processed=False)

    if len(not_processed_email) > 0:
        logger.debug('about to process {} emails'.format(
            len(not_processed_email))
        )

    for email in not_processed_email:

        attachment = None
        attachment_filename = ''
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
            attachment_filename=attachment_filename
        )
        if mail_send_success:
            email.processed = True
            email.save()
            logger.debug('successfully sent {}'.format(email))
        else:
            logger.error('unable to sent {}'.format(email))
