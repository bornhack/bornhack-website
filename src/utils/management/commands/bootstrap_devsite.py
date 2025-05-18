from __future__ import annotations

import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from utils.bootstrap.base import Bootstrap

logger = logging.getLogger(f"bornhack.{__name__}")

class Command(BaseCommand):
    args = "none"
    help = "Create mock data for development instances"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "-s",
            "--skip-auto-scheduler",
            action="store_true",
            help="Don't run the auto-scheduler. This is useful on operating systems for which the solver binary is not packaged, such as OpenBSD.",
        )

    def output(self, message) -> None:
        self.stdout.write(
            "{}: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message),
        )

    def handle(self, *args, **options) -> None:
        start = timezone.now()
        self.output(
            self.style.SUCCESS(
                "----------[ Deleting all data from database ]----------",
            ),
        )
        call_command("flush", "--noinput")
        bootstrap = Bootstrap()
        bootstrap.output = self.output
        bootstrap.bootstrap_full(options)
        duration = timezone.now() - start
        self.output(f"bootstrap_devsite took {duration}!")
