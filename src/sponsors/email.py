import os
import logging

from django.conf import settings

from utils.email import add_outgoing_email

logger = logging.getLogger("bornhack.%s" % __name__)

def add_sponsorticket_email(ticket):
    # put formatdict together
    formatdict = {
        "ticket": ticket,
    }

    subject = "%s %s Sponsor Ticket %s" % (
        ticket.sponsor.camp.title,
        ticket.sponsor.name,
        ticket.uuid,
    )

    filename = "sponsor_ticket_{}.pdf".format(ticket.pk)
    with open(os.path.join(settings.PDF_ARCHIVE_PATH, filename), "rb") as f:
        # add email to outgoing email queue
        return add_outgoing_email(
            text_template="emails/sponsorticket_email.txt",
            html_template="emails/sponsorticket_email.html",
            to_recipients=ticket.sponsor.ticket_email,
            formatdict=formatdict,
            subject=subject,
            attachment=f.read(),
            attachment_filename=filename,
        )

