from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from camps.models import Camp
from events.handler import handle_team_event

from .models import TicketType

logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    args = "none"
    help = "Post ticket stats to IRC"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "campslug",
            type=str,
            help="The slug of the camp to process",
        )

    def handle(self, *args, **options) -> None:
        camp = Camp.objects.get(slug=options["campslug"])
        output = self.format_shop_ticket_stats_for_irc(camp)
        for line in output:
            handle_team_event("ticket_stats", line)

    def format_shop_ticket_stats_for_irc(self):
        """Get stats for all tickettypes and return a list of strings max 200 chars long."""
        tickettypes = TicketType.objects.with_price_stats().filter(camp=self)
        output = []
        # loop over tickettypes and generate lines of max 200 chars
        for line in [
            f"{tt.name}: {tt.total_price} DKK/{tt.shopticket_count}={round(tt.average_price, 2)} DKK"
            for tt in tickettypes
        ]:
            if not output:
                # this is the start of the output
                output.append(line)
            elif len(output[-1]) + len(line) < 200:
                # add this line to the latest line of output
                output[-1] += f" ::: {line}"
            else:
                # add a new line of output to avoid going over linelength of 200
                output.append(line)
        return output
