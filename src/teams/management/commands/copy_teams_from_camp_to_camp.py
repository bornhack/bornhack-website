from __future__ import annotations

import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from utils.bootstrap.base import Bootstrap
from camps.models import Camp
from teams.models import Team

logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    args = "none"
    help = "Create camp teams based on a different camp"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "from-camp-slug",
            help="The slug of the camp to copy teams from, like bornhack-2016",
        )
        parser.add_argument(
            "to-camp-slug",
            help="The slug of the camp to copy teams to, like bornhack-2017",
        )

    def output(self, message) -> None:
        self.stdout.write(
            "{}: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message),
        )

    def handle(self, *args, **options) -> None:
        fromcamp = Camp.objects.get(slug=options["from-camp-slug"])
        tocamp = Camp.objects.get(slug=options["to-camp-slug"])
        self.output(
            self.style.SUCCESS(
                f"----------[ Copying teams from {fromcamp.title} to {tocamp.title} ]----------",
            ),
        )
        for team in fromcamp.teams.all():
            newteam, created = Team.objects.get_or_create(
                camp=tocamp,
                name=team.name,
                defaults={"description": team.description},
            )
            if created:
                print(f"Created new team {newteam}")
        self.output(
            self.style.SUCCESS(
                f"----------[ Done creating teams! ]----------",
            ),
        )
