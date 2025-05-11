import logging
import os

from django.conf import settings

from teams.models import Team
from utils.email import add_outgoing_email

logger = logging.getLogger("bornhack.%s" % __name__)


def add_sponsorticket_email(ticket):
    # put formatdict together
    formatdict = {
        "ticket": ticket,
    }

    subject = f"{ticket.sponsor.camp.title} {ticket.sponsor.name} Sponsor Ticket {ticket.uuid}"

    filename = f"sponsor_ticket_{ticket.pk}.pdf"
    with open(os.path.join(settings.PDF_ARCHIVE_PATH, filename), "rb") as f:
        # add email to outgoing email queue
        return add_outgoing_email(
            responsible_team=Team.objects.get(
                camp=ticket.sponsor.camp,
                name="Sponsors",
            ),
            text_template="emails/sponsorticket_email.txt",
            html_template="emails/sponsorticket_email.html",
            to_recipients=ticket.sponsor.ticket_email,
            formatdict=formatdict,
            subject=subject,
            attachment=f.read(),
            attachment_filename=filename,
        )
