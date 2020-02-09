# coding: utf-8
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from camps.models import Camp
from sponsors.models import Sponsor
from sponsors.email import add_sponsorticket_email

logger = logging.getLogger("bornhack.%s" % __name__)


class Command(BaseCommand):
    help = "Emails sponsor tickets"

    def add_arguments(self, parser):
        parser.add_argument("camp_slug", type=str)

    def output(self, message):
        self.stdout.write(
            "{}: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message)
        )

    def handle(self, *args, **options):
        camp = Camp.objects.get(slug=options["camp_slug"])
        sponsors = Sponsor.objects.filter(tier__camp=camp, tickets_generated=True)

        for sponsor in sponsors:
            if (
                sponsor.tier.tickets
                and sponsor.tickets_generated
                and sponsor.ticket_email
                and sponsor.ticket_ready
                and not sponsor.tickets_sent
            ):
                self.output(
                    "# Generating outgoing emails to send tickets for {}:".format(
                        sponsor
                    )
                )
                for ticket in sponsor.sponsorticket_set.all():
                    # send the email
                    if add_sponsorticket_email(ticket=ticket):
                        logger.info("OK: email to %s added" % sponsor)
                    else:
                        logger.error(
                            "Unable to send sponsor ticket email to %s" % sponsor
                        )

                sponsor.tickets_sent = True
                sponsor.save()
