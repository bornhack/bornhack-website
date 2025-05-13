"""Tests for token views."""

from __future__ import annotations

from bs4 import BeautifulSoup
from django.urls import reverse

from tokens.models import Token
from utils.tests import BornhackTestBase


class TestTokenViews(BornhackTestBase):
    """Test Phonebook view."""

    token: Token

    @classmethod
    def setUpTestData(cls) -> None:
        """Add test data."""
        # first add users and other basics
        super().setUpTestData()
        # then create some tokens
        cls.token = Token(
            camp=cls.camp,
            token="DEADBEAF1234",
            description="Test token",
            category="Test",
            active=True,
        )
        cls.token.save()

    def test_token_list_view(self) -> None:
        """Test the basics of the token list view."""
        self.client.login(username="user0", password="user0")
        url = reverse("tokens:tokenfind_list")

        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div#main > div > div > div > div > table > tbody > tr")
        self.assertEqual(len(rows), 3, "token list does not return 3 entries (camp name, header and token)")

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
        self.assertEqual(len(matches), 1, "token_find failed")

        # Test finding a false token
        url = reverse("tokens:details", kwargs={"token": "F00000001234"})
        response = self.client.get(path=url, follow=True)
        self.assertEqual(response.status_code, 404, "Did not find a non-excisting token")

