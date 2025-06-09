"""Base file for tests."""

from __future__ import annotations

import logging
from unittest import skip

from django.core.management import call_command
from django.test import Client
from django.test import TestCase

from camps.models import Camp
from teams.models import Team
from utils.bootstrap.base import Bootstrap


class TestBootstrapScript(TestCase):
    """Test bootstrap_devsite script (touching many codepaths)"""

    @skip
    def test_bootstrap_script(self):
        """If no orders have been made, the product is still available."""
        call_command("bootstrap_devsite")


class BornhackTestBase(TestCase):
    """Bornhack base TestCase."""

    users: dict
    camp: Camp
    team: Team
    bootstrap: Bootstrap

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        # disable logging
        logging.disable(logging.WARNING)

        cls.client = Client(enforce_csrf_checks=False)

        cls.bootstrap = Bootstrap()
        cls.bootstrap.bootstrap_tests()
        cls.camp = cls.bootstrap.camp
        cls.users = cls.bootstrap.users
        cls.teams = cls.bootstrap.teams
