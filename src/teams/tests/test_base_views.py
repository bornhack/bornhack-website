"""Test cases for the base and member views of the teams application."""

from __future__ import annotations

from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from camps.models import Permission as CampPermission
from teams.models import TeamMember
from utils.tests import BornhackTestBase


class TeamBaseMemberViewTest(BornhackTestBase):
    """Test Team Base and Member Views."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup test data."""
        # first add users and other basics
        super().setUpTestData()

        cls.categories = cls.bootstrap.create_camp_info_categories(camp=cls.camp, teams=cls.teams)
        cls.bootstrap.create_camp_info_items(camp=cls.camp, categories=cls.categories)

        permission_content_type = ContentType.objects.get_for_model(CampPermission)
        cls.users[4].user_permissions.add(
            Permission.objects.get(
                content_type=permission_content_type,
                codename="noc_team_lead",
            ),
        )

    def test_team_general_view(self) -> None:
        """Test the team general view."""
        url = reverse(
            "teams:general",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

    def test_team_list_view(self) -> None:
        """Test the team list view."""
        url = reverse(
            "teams:list",
            kwargs={
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

    def test_team_manage_view(self) -> None:
        """Test the team manage view."""
        self.client.force_login(self.users[4])
        url = reverse(
            "teams:manage",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

    def test_team_join_leave_view(self) -> None:
        """Test the team member join and leave view."""
        self.client.force_login(self.users[0])
        url = reverse(
            "teams:join",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

        response = self.client.post(path=url, follow=True)

        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "You request to join the team" in str(s)]
        self.assertEqual(len(matches), 1, "failed to join a team.")

        # Try to join the team twice.
        response = self.client.get(path=url, follow=True)

        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-warning")
        matches = [s for s in rows if "You are already a member of this team" in str(s)]
        self.assertEqual(len(matches), 1, "member was able to join twice.")

        # Try to join a team that does not need members
        url = reverse(
            "teams:join",
            kwargs={
                "team_slug": self.teams["orga"].slug,
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url, follow=True)

        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-warning")
        matches = [s for s in rows if "This team does not need members right now" in str(s)]
        self.assertEqual(len(matches), 1, "member was able to join a team which does not need members.")

        # Test leaving the team.
        url = reverse(
            "teams:leave",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

        response = self.client.post(path=url, follow=True)

        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "You are no longer a member of the team" in str(s)]
        self.assertEqual(len(matches), 1, "failed to leave a team.")

    def test_team_approve_remove_views(self) -> None:
        """Test team member approve and remove views."""
        self.client.force_login(self.users[8])
        url = reverse(
            "teams:join",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.post(path=url)
        assert response.status_code == 302

        member = TeamMember.objects.get(team=self.teams["noc"], user=self.users[8])

        self.client.force_login(self.users[4])
        # Approve the team member
        url = reverse(
            "teams:member_approve",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
                "pk": member.pk,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

        response = self.client.post(path=url, follow=True)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "Team member approved" in str(s)]
        self.assertEqual(len(matches), 1, "failed to approve a team member.")

        # Remove the team member
        url = reverse(
            "teams:member_remove",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
                "pk": member.pk,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

        response = self.client.post(path=url, follow=True)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "Team member removed" in str(s)]
        self.assertEqual(len(matches), 1, "failed to remove a team member.")
