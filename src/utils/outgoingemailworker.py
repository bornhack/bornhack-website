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

    for email in not_processed_email:
        if ',' in email.recipient:
            recipient = email.recipient.split(',')
        else:
            recipient = [email.recipient]

        _send_email(
            text_template=email.text_template,
            recipient=recipient,
            subject=email.subject,
            html_template=email.html_template,
            attachment=email.attachment,
            attachment_filename=email.attachment_filename
        )
