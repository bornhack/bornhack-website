from django.core.management.base import BaseCommand
from shop import invoiceworker
from time import sleep
import signal, sys
import logging


class Command(BaseCommand):
    args = 'none'
    help = 'Generate invoices and credit notes, and email invoices that have not been sent yet'
    exit = False

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('bornhack.%s' % __name__)

    def reload_worker_code(self, signum, frame):
        self.logger.info("Reloading shop.invoiceworker module...")
        reload(invoiceworker)
        self.logger.info("Done reloading shop.invoiceworker module")

    def clean_exit(self, signum, frame):
        self.logger.info("SIGTERM received, exiting gracefully soon...")
        self.exit = True

    def handle(self, *args, **options):
        self.logger.info("Connecting signals...")
        signal.signal(signal.SIGHUP, self.reload_worker_code)
        signal.signal(signal.SIGTERM, self.clean_exit)
        signal.signal(signal.SIGINT, self.clean_exit)

        self.logger.info("Entering main loop...")
        while True:
            # run invoiceworker
            invoiceworker.run_invoice_worker()

            # sleep for 60 seconds, but check sys.exit every second
            i = 0
            while i < 60:
                if self.exit:
                    self.logger.info("Graceful exit requested, calling sys.exit(0) now")
                    sys.exit(0)
                else:
                    i += 1
                    sleep(1)

