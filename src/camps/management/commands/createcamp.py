from __future__ import annotations

import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Creates html files needed for a camp"

    def add_arguments(self, parser) -> None:
        parser.add_argument("camp_slug", type=str)

    def output(self, message) -> None:
        self.stdout.write(
            "{}: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message),
        )

    def local_dir(self, entry):
        return os.path.join(settings.BASE_DIR, entry)

    def handle(self, *args, **options) -> None:
        # files to create, relative to BASE_DIR
        files = ["camps/templates/{camp_slug}_camp_detail.html"]

        # directories to create, relative to BASE_DIR
        dirs = ["static_src/img/{camp_slug}/logo"]

        camp_slug = options["camp_slug"]

        for _file in files:
            path = self.local_dir(_file.format(camp_slug=camp_slug))
            if os.path.isfile(_file):
                self.output(f"File {path} exists...")
            else:
                self.output(f"Creating {path}")
                with open(path, mode="w", encoding="utf-8") as f:
                    f.write(_file.format(camp_slug=camp_slug))

        for _dir in dirs:
            path = self.local_dir(_file.format(camp_slug=camp_slug))
            if os.path.exists(path):
                self.output(f"Path {path} exists...")
            else:
                self.output(f"Creating {path}")
                os.mkdir(path, mode=0o644)

        self.output("All there is left is to create:")
        self.output(
            self.local_dir(
                f"static_src/img/{camp_slug}/logo/{camp_slug}-logo-large.png",
            ),
        )
        self.output(
            self.local_dir(
                f"static_src/img/{camp_slug}/logo/{camp_slug}-logo-small.png",
            ),
        )
