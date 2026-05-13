"""Base file for tests."""

from __future__ import annotations

import logging
from argparse import ArgumentTypeError
from copy import deepcopy

import pytest
from django.core.management import CommandError
from django.core.management import call_command
from django.test import Client
from django.test import TestCase
from django.utils import timezone

from camps.models import Camp
from teams.models import Team
from utils.bootstrap.base import Bootstrap
from utils.management.commands import bootstrap_devsite


class TestBootstrapDevsiteCommand:
    """Test bootstrap_devsite command."""

    @pytest.fixture
    def options(self) -> dict:
        """Fixture for default options."""
        year = timezone.now().year
        return {
            "threads": 4,
            "skip_auto_scheduler": False,
            "writable_years": [i for i in range(year, year + 3)],
            "years": [i for i in range(2016, year + 6)],
        }

    def test_custom_years_type(self):
        """Test custom argument type for parsing years and returning a list."""
        cmd = bootstrap_devsite.Command()
        year = timezone.now().year
        expected = [year for year in range(year, (year + 3))]

        result = cmd._years(f"{year},{year + 2}")

        assert result == expected

    def test_custom_years_wrong_formatting(self):
        """Test raising exception when wrongly formatted."""
        cmd = bootstrap_devsite.Command()

        with pytest.raises(ArgumentTypeError):
            cmd._years("wrong format")

        with pytest.raises(ArgumentTypeError):
            cmd._years("2020-2021")

    def test_validating_threads_argument(self, options):
        """Test validating the `threads` arg."""
        cmd = bootstrap_devsite.Command()
        options["threads"] = 0

        with pytest.raises(CommandError):
            cmd.validate(options)

    def test_validating_years_is_not_below_2016(self, options):
        """Test validating `years` is not below 2016."""
        cmd = bootstrap_devsite.Command()
        copy = deepcopy(options)
        copy["years"][0] = 2015

        with pytest.raises(CommandError):
            cmd.validate(copy)

        with pytest.raises(CommandError):
            call_command("bootstrap_devsite", years=copy["years"])

    def test_validating_writable_years_is_within_range(self, options):
        """Validate writable years is within range of camp years."""
        cmd = bootstrap_devsite.Command()

        # Test lower limit
        lower = deepcopy(options)
        lower["writable_years"][0] = options["years"][0] - 1

        with pytest.raises(CommandError):
            cmd.validate(lower)

        with pytest.raises(CommandError):
            call_command(
                "bootstrap_devsite",
                writable_years=lower["writable_years"],
                years=lower["years"],
            )

        # Test upper limit
        upper = deepcopy(options)
        upper["writable_years"] = [i for i in range(min(upper["years"]), max(upper["years"]) + 2)]

        with pytest.raises(CommandError):
            cmd.validate(upper)

        with pytest.raises(CommandError):
            call_command(
                "bootstrap_devsite",
                writable_years=upper["writable_years"],
                years=upper["years"],
            )


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
