"""Test cases for the shift views of the teams application."""

from __future__ import annotations

from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone

from camps.models import Permission as CampPermission
from teams.models import TeamShift
from utils.tests import BornhackTestBase


class TeamShiftViewTest(BornhackTestBase):
    """Test Team Shift View"""

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup test data."""
        # first add users and other basics
        super().setUpTestData()
        permission_content_type = ContentType.objects.get_for_model(CampPermission)
        cls.users[4].user_permissions.add(
            Permission.objects.get(
                content_type=permission_content_type,
                codename="noc_team_lead",
            ),
        )

    def test_team_shift_requires_login(self) -> None:
        """Test viewing users team shifts requires to be signed in"""
        url = reverse(
            "teams:user_shifts",
            kwargs={
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(url)
        self.assertRedirects(response, f"/login/?next={url}")

    def test_team_shift_view_permissions(self) -> None:
        """Test the team shift view permissions."""
        self.client.force_login(self.users[0])  # Non noc team member
        # Test access control to the views
        url = reverse(
            "teams:shift_create",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 302

    def test_team_user_shift_view(self) -> None:
        """Test the user shift view."""
        self.client.force_login(self.users[4])  # Noc teamlead
        url = reverse(
            "teams:user_shifts",
            kwargs={
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

    def test_team_shift_views(self) -> None:
        """Test the team shift views."""
        self.client.force_login(self.users[4])  # Noc teamlead

        # Test creating a shift
        url = reverse(
            "teams:shift_create",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            data={
                "from_datetime": self.camp.buildup.lower.date(),
                "to_datetime": self.camp.buildup.lower + timezone.timedelta(hours=1),
                "people_required": 1,
            },
            follow=True,
        )
        assert response.status_code == 200
        content = response.content.decode()

        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 1, "team shift list does not return 1 entries after create")

        # Test same start and end.
        response = self.client.post(
            path=url,
            data={
                "from_datetime": self.camp.buildup.lower,
                "to_datetime": self.camp.buildup.lower,
                "people_required": 1,
            },
            follow=True,
        )
        assert response.status_code == 200
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("ul.list-unstyled.text-danger > li")
        matches = [s for s in rows if "Start can not be the same as end." in str(s)]
        self.assertEqual(len(matches), 1, "team shift Start can not be equal to end")

        # Test same end before start.
        response = self.client.post(
            path=url,
            data={
                "from_datetime": self.camp.buildup.lower + timezone.timedelta(hours=1),
                "to_datetime": self.camp.buildup.lower,
                "people_required": 1,
            },
            follow=True,
        )
        assert response.status_code == 200
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("ul.list-unstyled.text-danger > li")
        matches = [s for s in rows if "Start can not be after end." in str(s)]
        self.assertEqual(len(matches), 1, "team shift Start can not be before to end")

        # Test Creating multiple shifts
        url = reverse(
            "teams:shift_create_multiple",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
            },
        )

        response = self.client.get(url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            data={
                "from_datetime": self.camp.camp.lower.date(),
                "shift_length": 60,
                "number_of_shifts": 10,
                "people_required": 5,
            },
            follow=True,
        )
        assert response.status_code == 200

        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 11, "team shift list does not return 11 entries after create multiple")

        # Lookup the id of one of the shifts.
        shift_row = soup.select_one("table#main_table > tbody > tr:nth-of-type(1) td:nth-of-type(5)")
        shift_link = shift_row.find("a")
        shift_id = int(shift_link["href"].split("/")[5])

        # Test the update view
        url = reverse(
            "teams:shift_update",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
                "pk": shift_id,
            },
        )
        from_datetime = self.camp.buildup.lower
        to_datetime = from_datetime + timezone.timedelta(hours=2)

        response = self.client.get(url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            data={
                "from_datetime": from_datetime,
                "to_datetime": to_datetime,
                "people_required": 2,
            },
            follow=True,
        )
        assert response.status_code == 200

        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        row = soup.select_one("table#main_table > tbody > tr:nth-of-type(1) td:nth-of-type(3)").get_text(strip=True)
        self.assertEqual(row, "2", "team shift people required count does not return 2 entries after update")

        # Test the delete view
        url = reverse(
            "teams:shift_delete",
            kwargs={
                "team_slug": self.teams["noc"].slug,
                "camp_slug": self.camp.slug,
                "pk": shift_id,
            },
        )
        response = self.client.get(url)
        assert response.status_code == 200

        response = self.client.post(path=url, follow=True)
        assert response.status_code == 200
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 10, "team shift list does not return 10 entries after delete")

    def test_team_shift_actions(self) -> None:
        """Test the team shift actions."""
        self.client.force_login(self.users[4])  # Noc teamlead

        team_shift_1 = TeamShift(
            team=self.teams["noc"],
            shift_range=(
                self.camp.buildup.lower,
                self.camp.buildup.lower + timezone.timedelta(hours=1),
            ),
            people_required=1,
        )
        team_shift_1.save()
        team_shift_2 = TeamShift(
            team=self.teams["noc"],
            shift_range=(
                self.camp.buildup.lower,
                self.camp.buildup.lower + timezone.timedelta(hours=1),
            ),
            people_required=1,
        )
        team_shift_2.save()

        url = reverse(
            "teams:shift_member_take",
            kwargs={
                "team_slug": team_shift_1.team.slug,
                "camp_slug": self.camp.slug,
                "pk": team_shift_1.pk,
            },
        )
        response = self.client.get(
            path=url,
            follow=True,
        )
        assert response.status_code == 200
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select_one("table#main_table > tbody > tr:nth-of-type(1) td:nth-of-type(5)")
        matches = [s for s in rows if "Unassign me" in str(s)]
        self.assertEqual(len(matches), 1, "team shift assign failed")

        url = reverse(
            "teams:shift_member_take",
            kwargs={
                "team_slug": team_shift_1.team.slug,
                "camp_slug": self.camp.slug,
                "pk": team_shift_2.pk,
            },
        )
        response = self.client.get(
            path=url,
            follow=True,
        )
        assert response.status_code == 200
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-danger")
        matches = [s for s in rows if "overlapping" in str(s)]
        self.assertEqual(len(matches), 1, "team shift double assign failed to fail")

        url = reverse(
            "teams:shift_member_drop",
            kwargs={
                "team_slug": team_shift_1.team.slug,
                "camp_slug": self.camp.slug,
                "pk": team_shift_1.pk,
            },
        )

        response = self.client.get(
            path=url,
            follow=True,
        )
        assert response.status_code == 200
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select_one("table#main_table > tbody > tr:nth-of-type(1) td:nth-of-type(5)")
        matches = [s for s in rows if "Assign me" in str(s)]
        self.assertEqual(len(matches), 1, "team shift unassign failed")
