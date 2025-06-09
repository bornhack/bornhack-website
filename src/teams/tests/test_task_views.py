"""Test cases for the task views of the teams application."""

from __future__ import annotations

from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from camps.models import Permission as CampPermission
from utils.tests import BornhackTestBase


class TeamTaskViewTest(BornhackTestBase):
    """Test Team Task View"""

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup test data."""
        # first add users and other basics
        super().setUpTestData()
        permission_content_type = ContentType.objects.get_for_model(CampPermission)
        cls.users[4].user_permissions.add(
            Permission.objects.get(
                content_type=permission_content_type,
                codename="noc_team_tasker",
            ),
        )

    def test_team_task_view_permissions(self) -> None:
        """Test the team shift view permissions."""
        self.client.force_login(self.users[0]) # Non noc team member
        # Test access control to the views
        url = reverse("teams:task_create", kwargs={
            "team_slug": self.teams["noc"].slug,
            "camp_slug": self.camp.slug,
        })
        response = self.client.get(path=url)
        assert response.status_code == 403

    def test_team_task_views(self) -> None:
        """Test the team task views."""
        self.client.force_login(self.users[4]) # Noc team tasker
        url = reverse("teams:tasks", kwargs={
            "camp_slug": self.camp.slug,
            "team_slug": self.teams["noc"].slug,
        })
        response = self.client.get(path=url)
        assert response.status_code == 200

        # Test creating a shift
        url = reverse("teams:task_create", kwargs={
            "team_slug": self.teams["noc"].slug,
            "camp_slug": self.camp.slug,
        })
        response = self.client.get(url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            data={
                "name": "Test task",
                "description": "Test task description",
                "when_0": self.camp.buildup.lower,
                "when_1": self.camp.buildup.upper,
                },
            follow=True,
        )
        assert response.status_code == 200

        task = response.context["task"]

        # Test if the task got to the list.
        url = reverse("teams:tasks", kwargs={
            "camp_slug": self.camp.slug,
            "team_slug": self.teams["noc"].slug,
        })
        response = self.client.get(path=url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 1, "team task list does not return 1 entries after create")

        # Test updating a task.
        url = reverse("teams:task_update", kwargs={
            "camp_slug": self.camp.slug,
            "team_slug": self.teams["noc"].slug,
            "slug": task.slug,
        })

        response = self.client.get(path=url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            data={
                "name": "Test task",
                "description": "Test updating a task description",
                "when_0": self.camp.buildup.lower,
                "when_1": self.camp.buildup.upper,
                "completed": True,
                },
            follow=True,
        )
        assert response.status_code == 200

        # Test submitting a comment
        url = reverse("teams:task_detail", kwargs={
            "camp_slug": self.camp.slug,
            "team_slug": self.teams["noc"].slug,
            "slug": task.slug,
        })

        response = self.client.post(
                path=url,
                data={
                    "comment": "Some test comment",
                    },
                follow=True,
                )
        assert response.status_code == 200

        response = self.client.post(
                path=url,
                data={
                    "comment": "",
                    },
                follow=True,
                )
        assert response.status_code == 200

        # Test if the page returned a failure
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-danger")
        matches = [s for s in rows if "Something went wrong." in str(s)]
        self.assertEqual(len(matches), 1, "comment does not return a error msg.")
