# coding: utf-8
from django.core.management.base import BaseCommand
from django.utils import timezone

from camps.models import Camp
from sponsors.models import Sponsor
from tickets.models import SponsorTicket, TicketType


class Command(BaseCommand):
    help = 'Creates sponsor tickets'

    def add_arguments(self, parser):
        parser.add_argument('camp_slug', type=str,)
        parser.add_argument('ticket_type_pk', type=str,)

    def output(self, message):
        self.stdout.write('{}: {}'.format(
                timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                message
            )
        )

    def handle(self, *args, **options):
        ticket_type = TicketType.objects.get(pk=options['ticket_type_pk'])
        camp = Camp.objects.get(slug=options['camp_slug'])
        sponsors = Sponsor.objects.filter(tier__camp=camp, tickets_generated=False)

        for sponsor in sponsors:
            if sponsor.tier.tickets:
                self.output("# Generating tickets for {}:".format(sponsor))
                for _ in range(sponsor.tier.tickets):
                    ticket = SponsorTicket(sponsor=sponsor, ticket_type=ticket_type)
                    ticket.save()
                    ticket.generate_pdf()
                    self.output("- {}_ticket_{}.pdf".format(ticket.shortname, ticket.pk))
            else:
                self.output("{} is in tier {}, which has no tickets set.".format(sponsor, sponsor.tier))
