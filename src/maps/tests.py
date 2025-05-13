from __future__ import annotations

from unittest import mock

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.test import override_settings
from django.test.client import RequestFactory

from .views import MapProxyView
from .views import MissingCredentials

USER = "user"
PASSWORD = "password"


@override_settings(
    DATAFORDELER_USER=USER,
    DATAFORDELER_PASSWORD=PASSWORD,
)
class MapProxyViewTest(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

        self.allowed_endpoints = [
            "/GeoDanmarkOrto/orto_foraar_wmts/1.0.0/WMTS",
            "/Dkskaermkort/topo_skaermkort/1.0.0/wms",
            "/DHMNedboer/dhm/1.0.0/wms",
        ]

    def test_endpoint_not_allowed_raises_perm_denied(self):
        fix_request = self.rf.get("/maps/kfproxy/not/allowed/endpoint")

        with self.assertRaises(PermissionDenied):
            MapProxyView.as_view()(fix_request)

    def test_all_allowed_endpoints(self):
        for endpoint in self.allowed_endpoints:
            fix_request = self.rf.get("/maps/kfproxy" + endpoint)
            with self.subTest(request=fix_request):
                with mock.patch("maps.views.requests") as mock_req:
                    mock_req.get.return_value.status_code = 200
                    result = MapProxyView.as_view()(fix_request)

                self.assertEqual(result.status_code, 200)

    def test_sanitizing_path(self):
        fix_path = "/maps/kfproxy/DHMNedboer/dhm/1.0.0/wms?transparent=true"

        result = MapProxyView().sanitize_path(fix_path)

        self.assertEqual(result, "/DHMNedboer/dhm/1.0.0/wms?transparent=TRUE")

    def test_sanitizing_path_not_failing_without_query(self):
        fix_path = "/maps/kfproxy/DHMNedboer/dhm/1.0.0/wms"

        result = MapProxyView().sanitize_path(fix_path)

        self.assertEqual(result, "/DHMNedboer/dhm/1.0.0/wms")

    def test_append_credentials(self):
        fix_path = "/path"
        fix_result = fix_path + f"&username={USER}&password={PASSWORD}"

        result = MapProxyView().append_credentials(fix_path)

        self.assertEqual(result, fix_result)

    def test_append_credentials_raises_perm_denied_if_no_creds_is_set(self):
        with (
            self.settings(
                DATAFORDELER_USER="",
                DATAFORDELER_PASSWORD="",
            ),
            self.assertRaises(MissingCredentials),
        ):
            MapProxyView().append_credentials("path")
