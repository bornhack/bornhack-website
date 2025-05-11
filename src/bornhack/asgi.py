"""ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

from __future__ import annotations

import os

import django
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bornhack.settings")
django.setup()
application = get_default_application()
