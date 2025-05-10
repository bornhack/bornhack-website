import json
import logging
import re

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.serializers import serialize
from django.db.models import Q
from django.http import HttpResponse
from django.templatetags.static import static
from django.urls import reverse
from django.views.generic import View
from django.views.generic.base import TemplateView
from jsonview.views import JsonView
from PIL import ImageColor

from .mixins import LayerViewMixin
from .models import ExternalLayer
from .models import Feature
from .models import Layer
from camps.mixins import CampViewMixin
from profiles.models import Profile
from facilities.models import FacilityType
from utils.color import adjust_color
from utils.color import is_dark

logger = logging.getLogger("bornhack.%s" % __name__)


class MissingCredentials(Exception):
    pass


class MapMarkerView(TemplateView):
    """
    View for generating the coloured marker
    """

    template_name = "marker.svg"

    @property
    def color(self):
        return ImageColor.getrgb("#" + self.kwargs["color"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stroke1"] = self.color
        context["stroke0"] = (
            adjust_color(self.color, -0.4)
            if is_dark(self.color)
            else adjust_color(self.color)
        )
        context["fill0"] = (
            adjust_color(self.color, -0.4)
            if is_dark(self.color)
            else adjust_color(self.color)
        )
        context["fill1"] = self.color
        return context

    def render_to_response(self, context, **kwargs):
        return super().render_to_response(
            context,
            content_type="image/svg+xml",
            **kwargs,
        )


class MapView(CampViewMixin, TemplateView):
    """
    Global map view
    """

    template_name = "maps_map.html"
    context_object_name = "maps_map"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facilitytype_list"] = FacilityType.objects.filter(
            responsible_team__camp=self.camp,
        )
        context["layers"] = Layer.objects.filter(
            Q(responsible_team__camp=self.camp) | Q(responsible_team=None),
        )
        context["externalLayers"] = ExternalLayer.objects.filter(
            Q(responsible_team__camp=self.camp) | Q(responsible_team=None),
        )
        context["mapData"] = {
            "facilitytype_list": list(context["facilitytype_list"].values()),
            "layers": list(
                context["layers"].values(
                    "description",
                    "name",
                    "slug",
                    "uuid",
                    "icon",
                    "invisible",
                    "group__name",
                ),
            ),
            "externalLayers": list(context["externalLayers"].values()),
            "villages": reverse(
                "villages_geojson",
                kwargs={"camp_slug": self.camp.slug},
            ),
            "people": reverse("maps:map_layer_profile"),
            "loggedIn": self.request.user.is_authenticated,
            "grid": static("json/grid.geojson"),
        }
        for facility in context["mapData"]["facilitytype_list"]:
            facility["url"] = reverse(
                "facilities:facility_list_geojson",
                kwargs={
                    "camp_slug": self.camp.slug,
                    "facility_type_slug": facility["slug"],
                },
            )
        for layer in context["mapData"]["layers"]:
            layer["url"] = reverse(
                "maps:map_layer_geojson",
                kwargs={"layer_slug": layer["slug"]},
            )
        return context


class LayerProfileLocationsView(JsonView):
    """
    Profile locations layer view.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = json.loads(
            serialize(
                "geojson",
                Profile.objects.filter(location__isnull=False),
                geometry_field="location",
                fields=[
                    "public_credit_name",
                ],
            ),
        )
        return context


class LayerGeoJSONView(LayerViewMixin, JsonView):
    """
    GeoJSON export view
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = json.loads(
            serialize(
                "geojson",
                Feature.objects.filter(layer=self.layer.uuid),
                geometry_field="geom",
                fields=[
                    "name",
                    "description",
                    "color",
                    "url",
                    "icon",
                    "topic",
                    "processing",
                ],
            ),
        )
        return context


class MapProxyView(View):
    """
    Proxy for Datafordeler map service. Created so we can show maps without
    leaking the IP of our visitors.
    """

    PROXY_URL = "/maps/kfproxy"
    VALID_ENDPOINTS = [
        "/GeoDanmarkOrto/orto_foraar_wmts/1.0.0/WMTS",
        "/GeoDanmarkOrto/orto_foraar/1.0.0/WMS",
        "/Dkskaermkort/topo_skaermkort/1.0.0/wms",
        "/DHMNedboer/dhm/1.0.0/wms",
    ]

    def get(self, *args, **kwargs):
        """
        Before we make the request we check that the path is in our whitelist.
        Before we return the response we copy headers except for a list we dont want.
        """

        # Raise PermissionDenied if endpoint isn't valid
        self.is_endpoint_valid(self.request.path)

        # Sanitize the query
        path = self.sanitize_path(self.request.get_full_path())

        # Add credentials to query
        path = self.append_credentials(path)

        # make the request
        r = requests.get("https://services.datafordeler.dk" + path)

        # make the response
        response = HttpResponse(r.content, status=r.status_code)

        # list of headers that cause trouble when proxying
        excluded_headers = [
            "connection",
            "content-encoding",
            "content-length",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
        ]
        # proxy all headers from our upstream request to the response to our client,
        # if the headers are not in our list of troublemakers
        for key, value in r.headers.items():
            if key.lower() not in excluded_headers:
                response[key] = value

        # all good, return the response
        return response

    def is_endpoint_valid(self, path: str) -> None:
        """Validate request path against whitelisted endpoints or raise PermDenied"""
        endpoint = path.replace(self.PROXY_URL, "", 1)
        if endpoint not in self.VALID_ENDPOINTS:
            logger.warning(
                "Maps endpoint was invalid: '%s' valid endpoints: %s",
                endpoint,
                self.VALID_ENDPOINTS,
            )
            raise PermissionDenied("No thanks")

    def sanitize_path(self, path: str) -> str:
        """Sanitize path by removing PROXY_URL and set 'transparent' value to upper"""
        new_path = path.replace(self.PROXY_URL, "", 1)
        sanitized_path = re.sub(
            r"(transparent=)(true|false)",
            lambda match: rf"{match.group(1)}{match.group(2).upper()}",
            new_path,
        )
        return sanitized_path

    def append_credentials(self, path: str) -> str:
        """Verify credentials are defined in settings & append or raise exception"""
        username = settings.DATAFORDELER_USER
        password = settings.DATAFORDELER_PASSWORD
        if not username or not password:
            logger.error(
                "Missing credentials for "
                "'DATAFORDELER_USER' or 'DATAFORDELER_PASSWORD'",
            )
            raise MissingCredentials()
        path += f"&username={username}&password={password}"
        return path
