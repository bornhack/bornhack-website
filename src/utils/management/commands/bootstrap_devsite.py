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

from camps.models import Camp
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
            default=2,
            help="Specify amount of threads to be used. Default: 2",
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
            default=[i for i in range(2016, 2032)],
            help="Comma separated range of camp years. Example: 2016,2032",
        )

    def _years(self, value: str) -> list[int]:
        """Transform str argument to list of years or raise exception."""
        try:
            years = [int(year.strip()) for year in value.split(",")]
            return [year for year in range(min(years), max(years) + 1)]
        except ValueError:
            raise ArgumentTypeError(
                "Years must be comma separated integers (e.g. 2026,2027)"
            )

    def handle(self, *args, **options) -> None:
        """Flush database and run bootstrapper."""
        start = timezone.now()

        self.validate(options)
        self.decorated_output("Flush all data from database", "yellow")
        call_command("flush", "--noinput")

        bootstrap = Bootstrap()
        bootstrap.output = self.output
        self.run(bootstrap, options)

        duration = timezone.now() - start
        self.decorated_output(
            f"Finished bootstrap_devsite in {duration}!",
            "green"
        )

    def validate(self, options: dict):
        """Validate arguments parsed to command."""
        threads = options["threads"]
        if threads is not None:
            if threads < 1:
                raise CommandError("When specifying threads it must be above 0")

        years = options["years"]
        if years is not None:
            if min(years) < 2016:
                raise CommandError("When specifying years the lower limit is 2016")

        writables = options["writable_years"]
        if writables is not None:
            if min(writables) < min(years) or max(writables) > max(years):
                raise CommandError(
                    "When specifying writable years stay within range of years"
                )

    def run(self, bootstrap: Bootstrap, options: dict):
        """Bootstrap data using threading."""
        self.decorated_output(f"Running bootstrap_devsite", "green")

        years = options["years"]
        writable_years = options["writable_years"]
        prepared_camps = bootstrap.prepare_camp_list(years, writable_years)
        bootstrap.bootstrap_global_data(prepared_camps)
        self.decorated_output(years, "red")

        threads = options["threads"]
        self.decorated_output(
            f"Bootstrap camp data using {threads} threads",
            "green"
        )

        # Don't bootstrap above last writable camp
        BOOTSTRAP_LIMIT = writable_years[-1]
        bootstrap_logs = []
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for camp in bootstrap.camps:
                if camp.year > BOOTSTRAP_LIMIT:
                    bootstrap_logs.append(
                        (f"Skipping bootstrap for {camp.title}", "yellow")
                    )
                else:
                    executor.submit(
                        self.worker_job,
                        bootstrap,
                        camp,
                        (not options["skip_auto_scheduler"]),
                        False if camp.year in writable_years else True
                    )
                    bootstrap_logs.append(
                        (f"Completed bootstrapping of {camp.title}", "green")
                    )

        bootstrap.post_bootstrap()

        for msg, style in bootstrap_logs:
            self.decorated_output(msg, style)

    def worker_job(
        self,
        bootstrap: Bootstrap,
        camp: Camp,
        schedule: bool,
        read_only: bool
    ):
        """Execute concurrent bootstrapping atomically
        and always close the db connection.
        """
        try:
            with transaction.atomic():
                bootstrap.bootstrap_camp(camp, schedule, read_only)
        finally:
            connections.close()

    def decorated_output(self, msg, style=None):
        """Decorate the stdout format with color and ascii art."""
        msg = f"----------[ {msg} ]----------"
        if style:
            color_map = {
                "red": self.style.ERROR,
                "yellow": self.style.WARNING,
                "green": self.style.SUCCESS,
            }
            color = color_map.get(style, self.style.NOTICE)
            msg = color(msg)
        self.output(msg)

    def output(self, message) -> None:
        """Format the stdout format for command."""
        self.stdout.write(
            "{}: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message),
        )

