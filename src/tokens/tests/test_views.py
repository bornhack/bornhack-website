"""Tests for token views."""

from __future__ import annotations

from datetime import datetime

import pytz
from bs4 import BeautifulSoup
from django.urls import reverse

from tokens.models import Token
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

        # then create some tokens
        cls.token = Token(
            camp=cls.camp,
            token="DEADBEAF1234",
            description="Test token",
            category="Test",
            active=True,
        )
        cls.token.save()

        cls.token_inactive = Token(
            camp=cls.camp,
            token="1234DEADBEAF",
            description="Test Inactive token",
            category="Test",
            active=False,
        )
        cls.token_inactive.save()

        cls.token_timed_old = Token(
            camp=cls.camp,
            token="12341337F01F",
            description="Test timed token",
            category="Test",
            active=True,
            valid_when=["2000-01-01 00:00:00", "2000-10-10 10:10:10"],
        )
        cls.token_timed_old.save()

        cls.token_timed_current = Token(
            camp=cls.camp,
            token="12341337F02F",
            description="Test timed token",
            category="Test",
            active=True,
            valid_when=[now, datetime(year + 1, 1, 1, 1, 1, tzinfo=tz)],
        )
        cls.token_timed_current.save()

        cls.token_timed_new = Token(
            camp=cls.camp,
            token="12341337F03F",
            description="Test timed token",
            category="Test",
            active=True,
            valid_when=[datetime(year + 1, 1, 1, 1, 1, tzinfo=tz), datetime(year + 1, 12, 1, 1, 1, tzinfo=tz)],
        )
        cls.token_timed_new.save()

    def test_token_list_view(self) -> None:
        """Test the basics of the token list view."""
        self.client.login(username="user0", password="user0")
        url = reverse("tokens:tokenfind_list")

        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div#main > div > div > div > div > table > tbody > tr")
        self.assertEqual(len(rows), 6, "token list does not return 6 entries (camp name, header and tokens)")

    def test_token_find_view(self) -> None:
        """Test the basics of the token find view."""
        self.client.login(username="user0", password="user0")

        url = reverse("tokens:details", kwargs={"token": self.token.token})

        # Test finding the test token
        response = self.client.get(path=url, follow=True)
        assert response.status_code == 200

        # Test if the page returned a success
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "You found a secret token:" in str(s)]
        self.assertEqual(len(matches), 1, "token find does not return the found msg.")

        # Test finding a false token
        url = reverse("tokens:details", kwargs={"token": "F00000001234"})
        response = self.client.get(path=url, follow=True)
        self.assertEqual(response.status_code, 404, "Did not find a non-existing token")

        # Test finding a inactive token
        url = reverse("tokens:details", kwargs={"token": self.token_inactive.token})
        response = self.client.get(path=url, follow=True)
        assert response.status_code == 200

        # Test if the page returned a warning
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-warning")
        matches = [s for s in rows if "Patience!" in str(s)]
        self.assertEqual(len(matches), 1, "inactive token find does not return the Patience msg.")

        # Test finding a time expired token
        url = reverse("tokens:details", kwargs={"token": self.token_timed_old.token})
        response = self.client.get(path=url, follow=True)
        assert response.status_code == 200

        # Test if the page returned a warning
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-warning")
        matches = [s for s in rows if "This token is not valid after" in str(s)]
        self.assertEqual(len(matches), 1, "inactive token find does not return the not valid after msg.")

        # Test finding a timed token
        url = reverse("tokens:details", kwargs={"token": self.token_timed_current.token})
        response = self.client.get(path=url, follow=True)
        assert response.status_code == 200

        # Test if the page returned a success
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "You found a secret token:" in str(s)]
        self.assertEqual(len(matches), 1, "token find does not return the found msg.")

        # Test finding a timed not active yet token
        url = reverse("tokens:details", kwargs={"token": self.token_timed_new.token})
        response = self.client.get(path=url, follow=True)
        assert response.status_code == 200

        # Test if the page returned a warning
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-warning")
        matches = [s for s in rows if "This token is not valid yet" in str(s)]
        self.assertEqual(len(matches), 1, "inactive token find does not return the not valid yet.")
