from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from camps.models import Camp
from economy.utils import import_pos_data

logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    args = "none"
    help = "Import Pos sales data"

    def handle(self, *args, **options) -> None:
        """Run the import for all write enabled camps."""
        for camp in Camp.objects.filter(read_only=False):
            import_pos_data(camp)
