"""Test cases for the Maps application."""

from __future__ import annotations

from bs4 import BeautifulSoup
from django.urls import reverse

from teams.models import Team 
from utils.tests import BornhackTestBase

class TeamGuideViewTest(BornhackTestBase):
    """Test Team Guide View"""

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup test data."""
        # first add users and other basics
        super().setUpTestData()


    def test_team_guide_views_permission(self) -> None:
        """Test the team guide view."""
        self.client.force_login(self.users[0])

        url = reverse("teams:guide", kwargs={"team_slug": self.team.slug, "camp_slug": self.camp.slug})
        response = self.client.get(path=url, follow=True)
        assert response.status_code == 403

        url = reverse("teams:guide_print", kwargs={"team_slug": self.team.slug, "camp_slug": self.camp.slug})
        response = self.client.get(path=url, follow=True)
        assert response.status_code == 403

