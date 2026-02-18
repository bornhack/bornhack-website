from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from argparse import ArgumentTypeError

from django.core.management import call_command
from django.core.management import CommandError
from django.core.management.base import BaseCommand
from django.db import connections
from django.db import transaction
from django.utils import timezone

from utils.bootstrap.base import Bootstrap

logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    """Class for `bootstrap_devsite` command."""
    args = "none"
    help = "Create mock data for development instances"

    def add_arguments(self, parser) -> None:
        """Define the arguments available for this command."""
        parser.add_argument(
            "-t",
            "--threads",
            type=int,
            default=4,
            help="Specify amount of threads to be used. Default: 4",
        )
        parser.add_argument(
            "-s",
            "--skip-auto-scheduler",
            action="store_true",
            help="Don't run the auto-scheduler. This is useful on operating systems for which the solver binary is not packaged, such as OpenBSD.",
        )
        parser.add_argument(
            "-w",
            "--writable-years",
            type=self._years,
            default=[timezone.now().year + i for i in range(2)],
            help="Comma separated range of writable years. Example: 2025,2027",
        )
        parser.add_argument(
            "-y",
            "--years",
            type=self._years,
            default=[2016, timezone.now().year + 6],
            help="Comma separated range of camp years. Example: 2016,2032",
        )

    def _years(self, value: str) -> list[int]:
        """Transform str argument to list of years or raise exception."""
        try:
            return [int(year.strip()) for year in value.split(",")]
        except ValueError:
            raise ArgumentTypeError(
                "Years must be comma separated integers (e.g. 2026,2027)"
            )

    def handle(self, *args, **options) -> None:
        """Flush database and run bootstrapper."""
        start = timezone.now()

        self.validate(options)
        self.decorated_output(
            "Flush all data from database",
            self.style.WARNING
        )
        call_command("flush", "--noinput")

        bootstrap = Bootstrap()
        bootstrap.output = self.output
        self.run(bootstrap, options)

        duration = timezone.now() - start
        self.decorated_output(
            f"Finished bootstrap_devsite in {duration}!",
            self.style.SUCCESS
        )

    def validate(self, options: dict):
        """Validate arguments parsed to command."""
        threads = options["threads"]
        if threads is not None:
            if threads < 1:
                raise CommandError("When specifying threads it must be above 0")

        years = options["years"]
        if years is not None:
            if years[0] < 2016:
                raise CommandError("When specifying years the lower limit is 2016")

        writable_years = options["writable_years"]
        if writable_years is not None:
            if writable_years[0] < years[0] or writable_years[1] > years[1]:
                raise CommandError(
                    "When specifying writable years stay within range of years"
                )

    def run(self, bootstrap:Bootstrap, options: dict):
        """Bootstrap data using threading."""
        self.decorated_output(f"Running bootstrap_devsite", self.style.SUCCESS)

        years = options["years"]
        writable_years = options["writable_years"]
        prepared_camps = bootstrap.prepare_camp_list(years, writable_years)
        camps = bootstrap.create_camps(prepared_camps)
        bootstrap.bootstrap_global_data()

        threads = options["threads"]
        self.decorated_output(
            f"Bootstrap camp data using {threads} threads",
            self.style.SUCCESS
        )

        # Don't bootstrap above last writable camp
        BOOTSTRAP_LIMIT = writable_years[1]
        limit_logs = []
        schedule = (not options["skip_auto_scheduler"])
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for camp in camps:
                if camp.year > BOOTSTRAP_LIMIT:
                    limit_logs.append(f"Not bootstrapping {camp.title}")
                else:
                    executor.submit(self.worker_job, bootstrap, camp, schedule)

        bootstrap.post_bootstrap(writable_years)

        for msg in limit_logs:
            self.decorated_output(msg, self.style.WARNING)

    def worker_job(self, bootstrap: Bootstrap, camp, autoschedule: bool):
        """Execute concurrent bootstrapping atomically
        and always close the db connection.
        """
        try:
            with transaction.atomic():
                bootstrap.bootstrap_camp(camp, autoschedule)
        finally:
            connections.close()

    def output(self, message) -> None:
        """Format the stdout format for command."""
        self.stdout.write(
            "{}: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message),
        )

    def decorated_output(self, msg, style=None):
        """Decorate the stdout format with color and ascii art"""
        msg = f"----------[ {msg} ]----------"
        if style:
            msg = style(msg)
        self.output(msg)

