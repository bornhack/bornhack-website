from __future__ import annotations

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from camps.models import Camp
from sponsors.email import add_sponsorticket_email
from sponsors.models import Sponsor

logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    help = "Emails sponsor tickets"

    def add_arguments(self, parser) -> None:
        parser.add_argument("camp_slug", type=str)

    def output(self, message) -> None:
        self.stdout.write(
            "{}: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message),
        )

    def handle(self, *args, **options) -> None:
        camp = Camp.objects.get(slug=options["camp_slug"])
        sponsors = Sponsor.objects.filter(
            tier__camp=camp,
            tickets_generated=True,
            ticket_ready=True,
            tickets_sent=False,
        )

        for sponsor in sponsors:
            if sponsor.ticket_email:
                self.output(
                    f"# Generating outgoing emails to send tickets for {sponsor}:",
                )
                for ticket in sponsor.sponsorticket_set.all():
                    # send the email
                    if add_sponsorticket_email(ticket=ticket):
                        logger.info(f"OK: email to {sponsor} added")
                    else:
                        logger.error(
                            f"Unable to send sponsor ticket email to {sponsor}",
                        )

                sponsor.tickets_sent = True
                sponsor.save()
