"""Base file for tests."""
from __future__ import annotations

import logging
from datetime import datetime
from unittest import skip

import pytz
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client
from django.test import TestCase

from camps.models import Camp


class TestBootstrapScript(TestCase):
    """Test bootstrap_devsite script (touching many codepaths)"""

    @skip
    def test_bootstrap_script(self):
        """If no orders have been made, the product is still available."""
        call_command("bootstrap_devsite")


class BornhackTestBase(TestCase):
    """Bornhack base TestCase."""
    users: list[User]
    camp: Camp

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        # disable logging
        logging.disable(logging.WARNING)

        cls.client = Client(enforce_csrf_checks=False)

        tz = pytz.timezone("Europe/Copenhagen")
        year = datetime.now(tz).year
        cls.camp = Camp(
            title="Test Camp",
            slug="test-camp",
            tagline="Such test much wow",
            shortslug="test-camp",
            buildup=(
                datetime(year, 8, 25, 12, 0, tzinfo=tz),
                datetime(year, 8, 27, 12, 0, tzinfo=tz),
            ),
            camp=(
                datetime(year, 8, 27, 12, 0, tzinfo=tz),
                datetime(year, 9, 3, 12, 0, tzinfo=tz),
            ),
            teardown=(
                datetime(year, 9, 3, 12, 0, tzinfo=tz),
                datetime(year, 9, 5, 12, 0, tzinfo=tz),
            ),
            colour="#ffffff",
            light_text=False,
        )
        cls.camp.save()

        cls.users = []
        user = User.objects.create_user(
            username="user0",
            email="user0@example.com",
        )
        user.set_password("user0")
        user.save()
        cls.users.append(user)
