from __future__ import annotations

import logging
from argparse import ArgumentTypeError
from concurrent.futures import ThreadPoolExecutor

from django.core.management import CommandError
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections
from django.db import transaction
from django.utils import timezone

from camps.models import Camp
from utils.bootstrap.base import Bootstrap

logger = logging.getLogger(f"bornhack.{__name__}")
VERBOSITY_LOG_LEVELS = {
    0: logging.ERROR,
    1: logging.WARNING,
    2: logging.INFO,
    3: logging.DEBUG,
}


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
            default=[i for i in range(2016, timezone.now().year + 6)],
            help="Comma separated range of camp years. Example: 2016,2032",
        )

    def _years(self, value: str) -> list[int]:
        """Transform str argument to list of years or raise exception."""
        try:
            years = [int(year.strip()) for year in value.split(",")]
            return [year for year in range(min(years), max(years) + 1)]
        except ValueError:
            raise ArgumentTypeError(
                "Years must be comma separated integers (e.g. 2026,2027)",
            )

    def handle(self, *args, **options) -> None:
        """Flush database and run bootstrapper."""
        start = timezone.now()
        self.decorated_output("Running bootstrap_devsite", "cyan")

        logging.getLogger(
            "bornhack",
        ).setLevel(VERBOSITY_LOG_LEVELS.get(options["verbosity"], 1))

        self.validate(options)

        self.decorated_output("Flush all data from database", "purple")
        call_command("flush", "--noinput")

        bootstrap = Bootstrap()
        bootstrap.output = self.output
        self.run(bootstrap, options)

        duration = timezone.now() - start
        self.decorated_output(
            f"Finished bootstrap_devsite in {duration}!",
            "cyan",
        )

    def validate(self, options: dict):
        """Validate arguments parsed to command."""
        threads = options["threads"]
        if threads is not None:
            if threads < 1:
                raise CommandError("When specifying threads it must be above 0")

        years = options["years"]
        if min(years) < 2016:
            raise CommandError("When specifying years the lower limit is 2016")

        writables = options["writable_years"]
        if min(writables) < min(years) or max(writables) > max(years):
            raise CommandError(
                "Writable years is not within range of camp years."
                "\nUse (-w/--writable-years YYYY,YYYY) for manual override.",
            )

    def run(self, bootstrap: Bootstrap, options: dict):
        """Bootstrap data using threading."""
        years = options["years"]
        writable_years = options["writable_years"]
        prepared_camps = bootstrap.prepare_camp_list(years, writable_years)

        self.decorated_output("Creating global data", "green")
        bootstrap.bootstrap_global_data(prepared_camps)
        self.decorated_output("Finished creating global data", "green")

        threads = options["threads"]
        self.decorated_output(
            f"Bootstrap camp data using {threads} threads",
            "purple",
        )

        # Don't bootstrap above last writable camp
        BOOTSTRAP_LIMIT = writable_years[-1]
        bootstrap_logs = []
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for camp in bootstrap.camps:
                if camp.year > BOOTSTRAP_LIMIT:
                    bootstrap_logs.append(
                        (f"Skipping bootstrap for {camp.title}", "yellow"),
                    )
                else:
                    executor.submit(
                        self.worker_job,
                        bootstrap,
                        camp,
                        (not options["skip_auto_scheduler"]),
                        False if camp.year in writable_years else True,
                    )
                    bootstrap_logs.append(
                        (f"Completed bootstrapping of {camp.title}", "green"),
                    )

        self.decorated_output("Running post bootstrap tasks", "purple")
        bootstrap.post_bootstrap()
        self.decorated_output("Finished post bootstrap tasks", "purple")

        for msg, style in bootstrap_logs:
            self.decorated_output(msg, style)

    def worker_job(
        self,
        bootstrap: Bootstrap,
        camp: Camp,
        schedule: bool,
        read_only: bool,
    ):
        """Execute concurrent bootstrapping atomically
        and always close the db connection.
        """
        self.decorated_output(f"Executing worker job: {camp.title}", "cyan")
        try:
            with transaction.atomic():
                bootstrap.bootstrap_camp(camp, schedule, read_only)
        finally:
            connections.close()

    def decorated_output(self, msg, color="white"):
        """Decorate stdout with colored text and ascii art."""
        msg = f"----------[ {msg} ]----------"
        self.output(msg, color)

    def output(self, msg, color="white") -> None:
        """Formatting stdout with colored text options."""
        color_map = {
            "red": self.style.ERROR,
            "yellow": self.style.WARNING,
            "green": self.style.SUCCESS,
            "white": self.style.HTTP_INFO,  # DEFAULT/FALLBACK
            "cyan": self.style.MIGRATE_HEADING,
            "purple": self.style.HTTP_SERVER_ERROR,
        }
        color = color_map.get(color, self.style.HTTP_INFO)
        self.stdout.write(
            "{}: {}".format(
                timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                color(msg),
            ),
        )
