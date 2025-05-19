"""Test cases for the info views of the teams application."""

from __future__ import annotations

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from camps.models import Permission as CampPermission
from utils.tests import BornhackTestBase


class TeamInfoViewTest(BornhackTestBase):
    """Test Team Info Views."""

    categories: dict

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
                codename="noc_team_infopager",
            ),
        )

    def test_team_info_view_permissions(self) -> None:
        """Test the team info view permissions."""
        self.client.force_login(self.users[0]) # Non noc team member
        # Test access control to the views
        url = reverse("teams:info_categories", kwargs={
            "team_slug": self.teams["noc"].slug,
            "camp_slug": self.camp.slug,
        })
        response = self.client.get(path=url)
        assert response.status_code == 403

    def test_team_info_views(self) -> None:
        """Test the team info views."""
        self.client.force_login(self.users[4]) # Noc teamlead

        # Test info categories page
        url = reverse("teams:info_categories", kwargs={
            "team_slug": self.teams["noc"].slug,
            "camp_slug": self.camp.slug,
        })
        response = self.client.get(url)
        assert response.status_code == 200

        # Test info categories create page
        url = reverse("teams:info_item_create", kwargs={
            "team_slug": self.teams["noc"].slug,
            "camp_slug": self.camp.slug,
            "category_anchor": self.categories["noc"].anchor,
        })
        response = self.client.get(url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            data={
                "category": self.categories["noc"].anchor,
                "headline": "Test info page",
                "body": "Some test info",
                "anchor": "test",
                "weight": 100,
                },
            follow=True,
        )
        assert response.status_code == 200

        # Test info categories edit page
        url = reverse("teams:info_item_update", kwargs={
            "team_slug": self.teams["noc"].slug,
            "camp_slug": self.camp.slug,
            "category_anchor": self.categories["noc"].anchor,
            "item_anchor": "test",
        })
        response = self.client.get(url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            data={
                "category": self.categories["noc"].anchor,
                "headline": "Test info page",
                "body": "Some test info",
                "anchor": "test",
                "weight": 101,
                },
            follow=True,
        )
        assert response.status_code == 200

        # Test info categories delete page
        url = reverse("teams:info_item_delete", kwargs={
            "team_slug": self.teams["noc"].slug,
            "camp_slug": self.camp.slug,
            "category_anchor": self.categories["noc"].anchor,
            "item_anchor": "test",
        })
        response = self.client.get(url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            follow=True,
        )
        assert response.status_code == 200
