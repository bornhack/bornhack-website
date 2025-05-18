"""Test cases for the base views of the teams application."""

from __future__ import annotations

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from camps.models import Permission as CampPermission
from utils.tests import BornhackTestBase


class TeamBaseViewTest(BornhackTestBase):
    """Test Team Base Views."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup test data."""
        # first add users and other basics
        super().setUpTestData()

        cls.categories = cls.bootstrap.create_camp_info_categories(camp=cls.camp, teams=cls.teams)
        cls.bootstrap.create_camp_info_items(camp=cls.camp,categories=cls.categories)

        permission_content_type = ContentType.objects.get_for_model(CampPermission)
        cls.users[4].user_permissions.add(
            Permission.objects.get(
                content_type=permission_content_type,
                codename="noc_team_lead",
            ),
        )
    def test_team_general_view(self) -> None:
        """Test the team general view."""
        url = reverse("teams:general", kwargs={
            "team_slug": self.teams["noc"].slug,
            "camp_slug": self.camp.slug,
        })
        response = self.client.get(path=url)
        assert response.status_code == 200

    def test_team_list_view(self) -> None:
        """Test the team list view."""
        url = reverse("teams:list", kwargs={
            "camp_slug": self.camp.slug,
        })
        response = self.client.get(path=url)
        assert response.status_code == 200

    def test_team_manage_view(self) -> None:
        """Test the team manage view."""
        self.client.force_login(self.users[4])
        url = reverse("teams:manage", kwargs={
            "team_slug": self.teams["noc"].slug,
            "camp_slug": self.camp.slug,
        })
        response = self.client.get(path=url)
        assert response.status_code == 200
