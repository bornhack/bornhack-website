from __future__ import annotations

import json
import logging

from django.core.management.base import BaseCommand

from economy.utils import import_pos_sales_json

logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    args = "none"
    help = "Import Pos sales JSON"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "jsonpath",
            type=str,
            help="The path to the Pos sales json file to import. The import is idempotent, no duplicates will be created.",
        )

    def handle(self, *args, **options) -> None:
        with open(options["jsonpath"]) as f:
            data = json.load(f)
            products, transactions, sales, costs = import_pos_sales_json(data)
            self.stdout.write(f"{products} new products created")
            self.stdout.write(f"{transactions} new transactions created")
            self.stdout.write(f"{sales} new sales created")
            self.stdout.write(f"{costs} new product_costs created")
