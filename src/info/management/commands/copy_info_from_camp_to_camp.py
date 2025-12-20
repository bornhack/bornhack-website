from __future__ import annotations

import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from camps.models import Camp
from info.models import InfoCategory, InfoItem

logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    args = "none"
    help = "Create infopages based on a different camp"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "from-camp-slug",
            help="The slug of the camp to copy info from, like bornhack-2016",
        )
        parser.add_argument(
            "to-camp-slug",
            help="The slug of the camp to copy info to, like bornhack-2017",
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
                f"----------[ Copying info from {fromcamp.title} to {tocamp.title} ]----------",
            ),
        )
        for team in fromcamp.teams.all():
            for infocat in team.info_categories.all():
                newteam = tocamp.teams.get(name=team.name)
                newcat, created = InfoCategory.objects.get_or_create(
                    headline=infocat.headline,
                    team=newteam,
                    defaults={
                        "anchor": infocat.anchor,
                        "weight": infocat.weight,
                    },
                )
                if created:
                    print(f"Created new InfoCategory {newcat}")
                for info in infocat.infoitems.all():
                    newinfo, created = InfoItem.objects.get_or_create(
                        category=newcat,
                        headline=info.headline,
                        defaults={
                            "anchor": info.anchor,
                            "body": info.body,
                            "weight": info.weight,
                        }
                    )
                    if created:
                        print(f"Created new InfoItem {newinfo}")
        self.output(
            self.style.SUCCESS(
                f"----------[ Done creating info! ]----------",
            ),
        )
