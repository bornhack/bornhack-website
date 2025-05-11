from django.core.management.base import BaseCommand
from django.utils import timezone

from camps.models import Camp
from sponsors.models import Sponsor
from tickets.models import SponsorTicket
from tickets.models import TicketType


class Command(BaseCommand):
    help = "Creates sponsor tickets"

    def add_arguments(self, parser):
        parser.add_argument("camp_slug", type=str)
        parser.add_argument("week_ticket_type_pk", type=str)
        parser.add_argument("day_ticket_type_pk", type=str)

    def output(self, message):
        self.stdout.write(
            "{}: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message),
        )

    def handle(self, *args, **options):
        week_ticket_type = TicketType.objects.get(pk=options["week_ticket_type_pk"])
        day_ticket_type = TicketType.objects.get(pk=options["day_ticket_type_pk"])
        camp = Camp.objects.get(slug=options["camp_slug"])
        sponsors = Sponsor.objects.filter(
            tier__camp=camp,
            ticket_ready=True,
            tickets_generated=False,
        )

        for sponsor in sponsors:
            # get week ticket count from Sponsor or fall back to tier
            week_tickets = sponsor.week_tickets if sponsor.week_tickets else sponsor.tier.week_tickets
            existing = SponsorTicket.objects.filter(
                sponsor=sponsor,
                ticket_type=week_ticket_type,
            ).count()
            missing = week_tickets - existing if week_tickets > existing else 0
            self.output(
                f"# Generating {missing} missing out of {week_tickets} total full week tickets for {sponsor}...",
            )
            for _ in range(missing):
                ticket = SponsorTicket(sponsor=sponsor, ticket_type=week_ticket_type)
                ticket.save()
                ticket.generate_pdf()
                self.output(
                    f"- {ticket.shortname}_ticket_{ticket.pk}.pdf",
                )
            # get oneday ticket count from Sponsor or fall back to tier
            oneday_tickets = sponsor.oneday_tickets if sponsor.oneday_tickets else sponsor.tier.oneday_tickets
            existing = SponsorTicket.objects.filter(
                sponsor=sponsor,
                ticket_type=day_ticket_type,
            ).count()
            missing = oneday_tickets - existing if oneday_tickets > existing else 0
            self.output(
                f"# Generating {missing} missing out of {oneday_tickets} total oneday tickets for {sponsor}...",
            )
            for _ in range(missing):
                ticket = SponsorTicket(sponsor=sponsor, ticket_type=day_ticket_type)
                ticket.save()
                ticket.generate_pdf()
                self.output(
                    f"- {ticket.shortname}_ticket_{ticket.pk}.pdf",
                )
            sponsor.tickets_generated = True
            sponsor.save()
