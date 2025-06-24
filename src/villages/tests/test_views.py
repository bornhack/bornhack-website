"""Test cases for the base and member views of the teams application."""

from __future__ import annotations

from bs4 import BeautifulSoup
from django.urls import reverse

from utils.tests import BornhackTestBase


class VillageViewTest(BornhackTestBase):
    """Test Village Views."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup test data."""
        # first add users and other basics
        super().setUpTestData()

        cls.bootstrap.create_camp_villages(camp=cls.camp, users=cls.users)

    def test_village_list_view(self) -> None:
        """Test the village list view."""
        url = reverse(
            "villages:village_list",
            kwargs={
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 2, "village list does not return 2 entries")

    def test_village_create_view(self) -> None:
        """Test the village create view."""
        self.client.force_login(self.users[0])
        url = reverse(
            "villages:village_create",
            kwargs={
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            data={
                "name": "Test Village",
                "description": "Some test village description.",
                "private": False,
                "location": """{"type":"Point","coordinates":[9.9401295,55.3881695]}""",
            },
            follow=True,
        )
        assert response.status_code == 200
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "Your request to create a village has been registered" in str(s)]
        self.assertEqual(len(matches), 1, "failed to create a village.")

        # Create village without location.
        response = self.client.post(
            path=url,
            data={
                "name": "Test Village",
                "description": "Some test village description.",
                "private": False,
                "location": "",
            },
            follow=True,
        )
        assert response.status_code == 200
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "Your request to create a village has been registered" in str(s)]
        self.assertEqual(len(matches), 1, "failed to create a village without location.")

    def test_village_geojson_view(self) -> None:
        """Test the village geojson view."""
        url = reverse(
            "villages:villages_geojson",
            kwargs={
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200
        content = response.json()
        self.assertEqual(len(content["features"]), 1, "GeoJSON view did not return 1 feature")

    def test_village_update_view(self) -> None:
        """Test the village update view."""
        self.client.force_login(self.users[2])
        url = reverse(
            "villages:village_update",
            kwargs={
                "camp_slug": self.camp.slug,
                "slug": "networkwarriors",
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            data={
                "name": "NetworkWarriors",
                "description": "Some test village description for NetworkWarriors.",
                "private": False,
                "location": """{"type":"Point","coordinates":[9.9401295,55.3881695]}""",
            },
            follow=True,
        )
        assert response.status_code == 200

        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.alert.alert-success")
        matches = [s for s in rows if "Your village will be republished after the changes have been reviewed" in str(s)]
        self.assertEqual(len(matches), 1, "failed to update a village.")

        url = reverse(
            "villages:village_update",
            kwargs={
                "camp_slug": self.camp.slug,
                "slug": "the-camp",
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 404

    def test_village_map_view(self) -> None:
        """Test the village map view."""
        url = reverse(
            "villages:village_map",
            kwargs={
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

    def test_village_detail_view(self) -> None:
        """Test the village detail view."""
        url = reverse(
            "villages:village_detail",
            kwargs={
                "camp_slug": self.camp.slug,
                "slug": "baconsvin",
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

        # Test 404 error page
        url = reverse(
            "villages:village_detail",
            kwargs={
                "camp_slug": self.camp.slug,
                "slug": "404camp",
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 404

        # Test accessing a not approved village.
        url = reverse(
            "villages:village_detail",
            kwargs={
                "camp_slug": self.camp.slug,
                "slug": "the-camp",
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 404

    def test_village_delete_view(self) -> None:
        """Test the village delete view."""
        self.client.force_login(self.users[0])
        url = reverse(
            "villages:village_create",
            kwargs={
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

        response = self.client.post(
            path=url,
            data={
                "name": "delete",
                "description": "Some delete test village description.",
                "private": False,
                "location": """{"type":"Point","coordinates":[9.9401295,55.3881695]}""",
            },
            follow=True,
        )
        assert response.status_code == 200

        url = reverse(
            "villages:village_delete",
            kwargs={
                "camp_slug": self.camp.slug,
                "slug": "delete",
            },
        )
        response = self.client.get(path=url)
        assert response.status_code == 200

        response = self.client.post(path=url, follow=True)
        assert response.status_code == 200
