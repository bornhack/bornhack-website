from unittest import mock

from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from django.core.exceptions import PermissionDenied

from .views import MapProxyView


class MapProxyViewTest(TestCase):

    def setUp(self):
        self.rf = RequestFactory()

        self.allowed_endpoints = [
            "/GeoDanmarkOrto/orto_foraar_wmts/1.0.0/WMTS",
            "/Dkskaermkort/topo_skaermkort/1.0.0/wms",
            "/DHMNedboer/dhm/1.0.0/wms"
        ]

        self.fix_user = "user"
        self.fix_pass = "pass"

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
        fix_result = (fix_path +
                      f"&username={self.fix_user}&password={self.fix_pass}")

        with self.settings(DATAFORDELER_USER=self.fix_user,
                           DATAFORDELER_PASSWORD=self.fix_pass):
            result = MapProxyView().append_credentials(fix_path)

        self.assertEqual(result, fix_result)

    def test_append_credentials_raises_perm_denied_if_no_creds_is_set(self):
        with self.settings(DATAFORDELER_USER="",
                           DATAFORDELER_PASSWORD=""):
            with self.assertRaises(Exception):
                MapProxyView().append_credentials("path")

