"""Tests for token views."""

from __future__ import annotations

from datetime import datetime

import pytz
from bs4 import BeautifulSoup
from django.urls import reverse

from tokens.models import Token
from tokens.models import TokenCategory
from utils.tests import BornhackTestBase


class TestTokenViews(BornhackTestBase):
    """Test Token view."""

    token: Token
    token_inactive: Token
    token_timed: Token
    token_timed_old: Token
    token_timed_current: Token
    token_timed_new: Token

    @classmethod
    def setUpTestData(cls) -> None:
        """Add test data."""
        # first add users and other basics
        super().setUpTestData()

        tz = pytz.timezone("Europe/Copenhagen")
        now = datetime.now(tz)
        year = now.year

        kwargs = {"camp_slug": cls.camp.slug}
        cls.url_dashboard = reverse(
            "tokens:dashboard",
            kwargs=kwargs
        )
        cls.url_submit = reverse(
            "tokens:submit",
            kwargs=kwargs
        )

        # create test category
        cls.category = TokenCategory(name="Test", description="Test category")
        cls.category.save()

        # then create some tokens
        cls.token = Token(
            camp=cls.camp,
            token="DEADBEAF1234",
            description="Test token",
            hint="Token1",
            category=cls.category,
            active=True,
        )
        cls.token.save()

        cls.token_inactive = Token(
            camp=cls.camp,
            token="1234DEADBEAF",
            description="Test Inactive token",
            hint="Token2",
            category=cls.category,
            active=False,
        )
        cls.token_inactive.save()

        cls.token_timed_old = Token(
            camp=cls.camp,
            token="12341337F01F",
            description="Test timed token",
            hint="Token3",
            category=cls.category,
            active=True,
            valid_when=["2000-01-01 00:00:00", "2000-10-10 10:10:10"],
        )
        cls.token_timed_old.save()

        cls.token_timed_current = Token(
            camp=cls.camp,
            token="12341337F02F",
            description="Test timed token",
            hint="Token4",
            category=cls.category,
            active=True,
            valid_when=[now, datetime(year + 1, 1, 1, 1, 1, tzinfo=tz)],
        )
        cls.token_timed_current.save()

        cls.token_timed_new = Token(
            camp=cls.camp,
            token="12341337F03F",
            description="Test timed token",
            hint="Token5",
            category=cls.category,
            active=True,
            valid_when=[datetime(year + 1, 1, 1, 1, 1, tzinfo=tz), datetime(year + 1, 12, 1, 1, 1, tzinfo=tz)],
        )
        cls.token_timed_new.save()

    def test_player_stats_in_context(self) -> None:
        """
        Test `player stats` values in context (only active tokens gets counted)
        """
        self.client.force_login(self.users[0])

        response = self.client.get(self.url_dashboard)
        result = response.context.get("player_stats")

        assert result.get("tokens_found") == 0
        assert result.get("tokens_missing") == 4
        assert result.get("tokens_count") == 4

    def test_dashboard_table_shows_active_tokens(self) -> None:
        """Test if all of the active tokens shows up in the dashboard table"""
        self.client.force_login(self.users[0])

        response = self.client.get(self.url_dashboard)
        decoded_content = response.content.decode()
        soup = BeautifulSoup(decoded_content, "html.parser")
        rows = soup.select("div#main table tbody tr")
        self.assertEqual(len(rows), 4, "The dashboard table does not show 4 rows")

    def test_token_find_view(self) -> None:
        """Test the basics of the token find view."""
        self.client.force_login(self.users[0])

        # Test finding the test token
        response = self.client.post(self.url_submit, {"token": self.token.token}, follow=True)
        assert response.status_code == 200

        # Test if the page returned a success
        decoded_content = response.content.decode()
        soup = BeautifulSoup(decoded_content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "You found a token:" in str(s)]
        self.assertEqual(len(matches), 1, "token find does not return the found msg.")

        # Test finding a false token
        response = self.client.post(self.url_submit, {"token": "F00000001234"}, follow=True)
        decoded_content = response.content.decode()
        soup = BeautifulSoup(decoded_content, "html.parser")
        rows = soup.select("div.alert.alert-danger")
        matches = [s for s in rows if "We did not recognize the token" in str(s)]
        self.assertEqual(len(matches), 1, "token find does not return the found msg.")

        # Test finding a inactive token
        response = self.client.post(self.url_submit, {"token": self.token_inactive.token}, follow=True)
        assert response.status_code == 200

        # Test if the page returned a warning
        decoded_content = response.content.decode()
        soup = BeautifulSoup(decoded_content, "html.parser")
        rows = soup.select("div.alert.alert-warning")
        matches = [s for s in rows if "Patience!" in str(s)]
        self.assertEqual(len(matches), 1, "inactive token find does not return the Patience msg.")

        # Test finding a time expired token
        response = self.client.post(self.url_submit, {"token": self.token_timed_old.token}, follow=True)
        assert response.status_code == 200

        # Test if the page returned a warning
        decoded_content = response.content.decode()
        soup = BeautifulSoup(decoded_content, "html.parser")
        rows = soup.select("div.alert.alert-warning")
        matches = [s for s in rows if "This token is not valid after" in str(s)]
        self.assertEqual(len(matches), 1, "inactive token find does not return the not valid after msg.")

        # Test finding a timed token
        response = self.client.post(self.url_submit, {"token": self.token_timed_current.token}, follow=True)
        assert response.status_code == 200

        # Test if the page returned a success
        decoded_content = response.content.decode()
        soup = BeautifulSoup(decoded_content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "Congratulations! You found a token:" in str(s)]
        self.assertEqual(len(matches), 1, "token find does not return the found msg.")

        # Test finding a timed not active yet token
        response = self.client.post(self.url_submit, {"token": self.token_timed_new.token}, follow=True)
        assert response.status_code == 200

        # Test if the page returned a warning
        decoded_content = response.content.decode()
        soup = BeautifulSoup(decoded_content, "html.parser")
        rows = soup.select("div.alert.alert-warning")
        matches = [s for s in rows if "This token is not valid yet" in str(s)]
        self.assertEqual(len(matches), 1, "inactive token find does not return the not valid yet.")
