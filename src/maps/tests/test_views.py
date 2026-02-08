"""Test cases for the Maps application."""

from __future__ import annotations

from unittest import mock

from bs4 import BeautifulSoup
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.test import override_settings
from django.test.client import RequestFactory
from django.urls import reverse

from maps.models import Group
from maps.models import Layer
from maps.models import UserLocation
from maps.models import UserLocationType
from maps.views import MapProxyView
from maps.views import MissingCredentialsError
from teams.models import TeamMember
from utils.tests import BornhackTestBase

USER = "user"
PASSWORD = "password"


@override_settings(
    DATAFORDELER_USER=USER,
    DATAFORDELER_PASSWORD=PASSWORD,
)
class MapProxyViewTest(TestCase):
    """Test the Proxy view."""

    def setUp(self):
        """Setup function."""
        self.rf = RequestFactory()

        self.allowed_endpoints = [
            "/GeoDanmarkOrto/orto_foraar_wmts/1.0.0/WMTS",
            "/GeoDanmarkOrto/orto_foraar/1.0.0/WMS",
            "/Dkskaermkort/topo_skaermkort/1.0.0/wms",
            "/DHMNedboer/dhm/1.0.0/wms",
        ]

    def test_endpoint_not_allowed_raises_perm_denied(self):
        """Test endpoint not allowed."""
        fix_request = self.rf.get("/maps/kfproxy/not/allowed/endpoint")

        with self.assertRaises(PermissionDenied):
            MapProxyView.as_view()(fix_request)

    def test_all_allowed_endpoints(self):
        """Test allowed endpoints."""
        for endpoint in self.allowed_endpoints:
            fix_request = self.rf.get("/maps/kfproxy" + endpoint)
            # Bug: pytest with pytest-xdist can't serialize objects, fixed in pytest v9.1
            # https://github.com/pytest-dev/pytest-xdist/issues/1273#issuecomment-3677708056
            # with self.subTest(request=fix_request):
            with mock.patch("maps.views.requests") as mock_req:
                mock_req.get.return_value.status_code = 200
                result = MapProxyView.as_view()(fix_request)

            self.assertEqual(result.status_code, 200)

    def test_sanitizing_path(self):
        """Test sanitization of paths."""
        fix_path = "/maps/kfproxy/DHMNedboer/dhm/1.0.0/wms?transparent=true"

        result = MapProxyView().sanitize_path(fix_path)

        self.assertEqual(result, "/DHMNedboer/dhm/1.0.0/wms?transparent=TRUE")

    def test_sanitizing_path_not_failing_without_query(self):
        """Test sanitization of paths without query."""
        fix_path = "/maps/kfproxy/DHMNedboer/dhm/1.0.0/wms"

        result = MapProxyView().sanitize_path(fix_path)

        self.assertEqual(result, "/DHMNedboer/dhm/1.0.0/wms")

    def test_append_credentials(self):
        """Test appending credentials."""
        fix_path = "/path"
        fix_result = fix_path + f"&username={USER}&password={PASSWORD}"

        result = MapProxyView().append_credentials(fix_path)

        self.assertEqual(result, fix_result)

    def test_append_credentials_raises_perm_denied_if_no_creds_is_set(self):
        """Test appending credentials exceptions."""
        with (
            self.settings(
                DATAFORDELER_USER="",
                DATAFORDELER_PASSWORD="",
            ),
            self.assertRaises(MissingCredentialsError),
        ):
            MapProxyView().append_credentials("path")


class MapsViewTest(BornhackTestBase):
    """Test Maps View"""

    layer: Layer
    hidden_layer: Layer
    group: Group

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup test data."""
        # first add users and other basics
        super().setUpTestData()

        # Create a layer
        cls.group = Group(name="Test Group")
        cls.group.save()
        cls.layer = Layer(
            name="Test layer 1",
            slug="test_1",
            description="Test Layer",
            icon="fas fa-tractor",
            group=cls.group,
            public=True,
            responsible_team=cls.teams["noc"],
        )
        cls.layer.save()

        cls.hidden_layer = Layer.objects.create(
            name="Non public layer",
            slug="hidden_layer",
            description="Hidden layer",
            icon="fa fa-list-ul",
            group=cls.group,
            public=False,
            responsible_team=cls.teams["noc"],
        )
        cls.hidden_layer.save()

        cls.users[0].save()
        teammember = TeamMember.objects.create(
            team=cls.teams["noc"],
            user=cls.users[0],
            approved=True,
            lead=True,
        )
        teammember.save()

    def test_geojson_layer_views(self) -> None:
        """Test the geojson view."""
        url = reverse("maps:map_layer_geojson", kwargs={"layer_slug": self.layer.slug})
        response = self.client.get(url)
        assert response.status_code == 200

        # test 404 of geojson layer
        url = reverse("maps:map_layer_geojson", kwargs={"layer_slug": "123test"})
        response = self.client.get(url)
        assert response.status_code == 404

        # test layer not being public
        url = reverse("maps:map_layer_geojson", kwargs={"layer_slug": self.hidden_layer.slug})
        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("p.lead")
        matches = [s for s in rows if "403" in str(s)]
        self.assertEqual(len(matches), 1, "geojson layer did not return a 403")

        # test layer access when not being public
        self.client.force_login(self.users[0])
        url = reverse("maps:map_layer_geojson", kwargs={"layer_slug": self.hidden_layer.slug})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_map_views(self) -> None:
        """Test the map view."""
        url = reverse("maps_map", kwargs={"camp_slug": self.camp.slug})
        response = self.client.get(url)
        assert response.status_code == 200

    def test_map_layer_json_view(self) -> None:
        """Test the map layers json view."""
        url = reverse("maps:map_layers_json")
        response = self.client.get(url)
        assert response.status_code == 200

    def test_marker_views(self) -> None:
        """Test the marker view."""
        good = ["ffffff", "ffffff00"]
        bad = ["ffff", "qwerty"]
        for color in good:
            url = reverse("maps:marker", kwargs={"color": color})
            response = self.client.get(url)
            assert response.status_code == 200

        for color in bad:
            url = reverse("maps:marker", kwargs={"color": color})
            response = self.client.get(url, raise_request_exception=True)
            assert response.status_code == 400


class MapsUserLocationViewTest(BornhackTestBase):
    """Test User Location Views"""

    user_location: UserLocation
    user_location_type: UserLocationType

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup test data."""
        super().setUpTestData()

        # Create user location type
        cls.user_location_type = UserLocationType(
            name="Test Type",
            slug="test",
            icon="fas fa-tractor",
            marker="blueIcon",
        )
        cls.user_location_type.save()

        # Create user location
        cls.user_location = UserLocation(
            name="Test User Location",
            type=cls.user_location_type,
            camp=cls.camp,
            user=cls.users[0],
            location=Point([9.940218, 55.388329]),
        )
        cls.user_location.save()

    def test_user_location_geojson_view(self) -> None:
        """Test the user location geojson view."""
        url = reverse(
            "maps_user_location_layer",
            kwargs={
                "camp_slug": self.camp.slug,
                "user_location_type_slug": self.user_location_type.slug,
            },
        )
        response = self.client.get(url)
        assert response.status_code == 200

    def test_user_location_view(self) -> None:
        """Test the user location list view."""
        self.client.force_login(self.users[0])
        url = reverse(
            "maps_user_location_list",
            kwargs={
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 1, "user location list does not return 1 entries")

    def test_user_location_create(self) -> None:
        """Test the user location create view."""
        self.client.force_login(self.users[0])
        url = reverse(
            "maps_user_location_create",
            kwargs={
                "camp_slug": self.camp.slug,
            },
        )
        response = self.client.post(
            path=url,
            data={
                "name": "Test User Location Create",
                "type": self.user_location_type.pk,
                "location": '{"type":"Point","coordinates":[9.940218,55.388329]}',
            },
            follow=True,
        )
        assert response.status_code == 200

        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 2, "user location list does not return 2 entries after create")
