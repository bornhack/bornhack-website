from __future__ import annotations

import importlib
import logging
import signal
import sys
from time import sleep

from django.core.management.base import BaseCommand

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    args = "none"
    help = "Run a worker. Takes the worker module as the first positional argument and calls the do_work() function in it. Optional arguments can be seen with -h / --help"
    exit_now = False

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "workermodule",
            type=str,
            help="The dotted path to the module which contains the do_work() function to call periodically.",
        )
        parser.add_argument(
            "--sleep",
            type=int,
            default=60,
            help="The number of seconds to sleep between calls",
        )

    def reload_worker(self, signum, frame) -> None:
        # we exit when we receive a HUP (expecting uwsgi or another supervisor to restart this worker)
        # this is more reliable than using importlib.reload to reload the workermodule code, since that
        # doesn't reload imports inside the worker module.
        logger.info(f"Signal {signum} (SIGHUP) received, exiting gracefully...")
        self.exit_now = True

    def clean_exit(self, signum, frame) -> None:
        logger.info(f"Signal {signum} (INT or TERM) received, exiting gracefully...")
        self.exit_now = True

    def handle(self, *args, **options) -> None:
        logger.info("Importing worker module...")
        self.workermodule = importlib.import_module(options["workermodule"])
        if not hasattr(self.workermodule, "do_work"):
            logger.error("module %s must have a do_work() method to call")
            sys.exit(1)

        logger.info("Connecting signals...")
        signal.signal(signal.SIGHUP, self.reload_worker)
        signal.signal(signal.SIGTERM, self.clean_exit)
        signal.signal(signal.SIGINT, self.clean_exit)

        logger.info("Entering main loop...")
        while True:
            try:
                # run worker code
                if not hasattr(self.workermodule, "do_work"):
                    raise NotImplementedError(
                        "Worker module should have a 'do_work' function.",
                    )
                self.workermodule.do_work()
            except Exception:
                logger.exception(
                    f"Got exception inside do_work for {self.workermodule}",
                )
                sys.exit(1)

            # sleep for N seconds before calling worker code again
            i = 0
            while i < options["sleep"]:
                # but check self.exit_now every second
                if self.exit_now:
                    sys.exit(0)
                else:
                    i += 1
                    sleep(1)
