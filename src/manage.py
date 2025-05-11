#!/usr/bin/env python
from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(__file__))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bornhack.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
