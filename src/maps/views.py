import json
import logging
import re

import requests
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.serializers import serialize
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic import ListView
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.views.generic import DeleteView
from django.views.generic.base import TemplateView
from jsonview.views import JsonView
from PIL import ImageColor
from leaflet.forms.widgets import LeafletWidget
from oauth2_provider.views.generic import ScopedProtectedResourceView

from .mixins import LayerViewMixin
from .models import ExternalLayer
from .models import Feature
from .models import Layer
from .models import UserLocation
from .models import UserLocationType
from camps.mixins import CampViewMixin
from utils.mixins import UserIsObjectOwnerMixin
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
        context["user_location_types"] = UserLocationType.objects.filter(
            user_locations__isnull=False,
        ).distinct()
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
            "user_location": list(
                context["user_location_types"].values(),
            ),
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
        for user_location_type in context["mapData"]["user_location"]:
            user_location_type["url"] = reverse(
                "maps_user_location_layer",
                kwargs={
                    "user_location_type_slug": user_location_type["slug"],
                    "camp_slug": self.camp.slug,
                },
            )
        return context


class LayerGeoJSONView(LayerViewMixin, JsonView):
    """
    GeoJSON export view
    """

    def get_context_data(self, **kwargs):
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


# User Location views


class LayerUserLocationView(CampViewMixin, JsonView):
    """
    UserLocation geojson view
    """

    def get_context_data(self, **kwargs):
        context = {}
        context["type"] = "FeatureCollection"
        context["features"] = self.dump_locations()
        return context

    def dump_locations(self) -> list[object]:
        """
        GeoJSON Formatter.
        """
        output = []
        for location in UserLocation.objects.filter(
            camp=self.camp,
            type__slug=self.kwargs["user_location_type_slug"],
        ):
            output.append(
                {
                    "type": "Feature",
                    "id": location.pk,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [location.location.x, location.location.y],
                    },
                    "properties": {
                        "name": location.name,
                        "type": location.type.name,
                        "icon": location.type.icon,
                        "marker": location.type.marker,
                        "user": location.user.profile.get_public_credit_name,
                        "data": location.data,
                    },
                },
            )
        return list(output)


class UserLocationListView(LoginRequiredMixin, CampViewMixin, ListView):
    template_name = "user_location_list.html"
    model = UserLocation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_location_types"] = UserLocationType.objects.all().values_list(
            "slug",
            flat=True,
        )
        return context

    def get_queryset(self, *args, **kwargs):
        """
        Show only entries belonging to the current user
        """
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(user=self.request.user)


class UserLocationCreateView(LoginRequiredMixin, CampViewMixin, CreateView):
    model = UserLocation
    template_name = "user_location_form.html"
    fields = ["name", "type", "location", "data"]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["location"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                "map_height": "500px",
                "geom_type": "Point",
                "class": "form-control",
            },
        )
        return form

    def form_valid(self, form):
        location = form.save(commit=False)
        location.camp = self.camp
        location.user = self.request.user
        location.save()
        messages.success(
            self.request,
            "New User Location created successfully.",
        )
        return redirect(
            reverse(
                "maps_user_location_list",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


class UserLocationUpdateView(
    LoginRequiredMixin,
    CampViewMixin,
    UserIsObjectOwnerMixin,
    UpdateView,
):
    model = UserLocation
    template_name = "user_location_form.html"
    fields = ["name", "type", "location", "data"]
    slug_url_kwarg = "user_location"
    slug_field = "pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {"grid": static("json/grid.geojson")}
        return context

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["location"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                "map_height": "500px",
                "geom_type": "Point",
                "class": "form-control",
            },
        )
        return form

    def get_success_url(self):
        return reverse(
            "maps_user_location_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class UserLocationDeleteView(
    LoginRequiredMixin,
    CampViewMixin,
    UserIsObjectOwnerMixin,
    DeleteView,
):
    model = UserLocation
    template_name = "user_location_delete.html"
    slug_url_kwarg = "user_location"
    slug_field = "pk"

    def get_success_url(self):
        messages.success(
            self.request,
            f"Your User Location {self.get_object().name} has been deleted successfully.",
        )
        return reverse(
            "maps_user_location_list",
            kwargs={"camp_slug": self.camp.slug},
        )


@method_decorator(csrf_exempt, name="dispatch")
class UserLocationApiView(
    ScopedProtectedResourceView,
    CampViewMixin,
    JsonView,
):
    required_scopes = ["location:write"]

    def get(self, request, **kwargs):
        if "user_location" not in kwargs:
            return HttpResponseNotAllowed(permitted_methods=["POST"])
        location = get_object_or_404(
            UserLocation,
            pk=kwargs["user_location"],
        )
        return {
            "pk": location.pk,
            "type": location.type.slug,
            "name": location.name,
            "lat": location.location.x,
            "lon": location.location.y,
            "data": location.data,
        }

    def post(self, request, **kwargs):
        if "user_location" in kwargs:
            return HttpResponseNotAllowed(permitted_methods=["GET", "PATCH", "DELETE"])
        data = json.loads(request.body)
        try:
            user_location_type = UserLocationType.objects.get(slug=data["type"])
        except UserLocationType.DoesNotExist:
            return {"error": "Type not found"}, 404
        location = UserLocation(
            user=request.user,
            location=Point(data["lat"], data["lon"]),
            name=data["name"],
            camp=self.camp,
            type=user_location_type,
        )
        if "data" in data:
            location.data = data["data"]
        location.save()

        return {
            "pk": location.pk,
            "type": location.type.slug,
            "name": location.name,
            "lat": location.location.x,
            "lon": location.location.y,
            "data": location.data,
        }

    def patch(self, request, **kwargs):
        if "user_location" not in kwargs and "camp_slug" not in kwargs:
            return HttpResponseNotAllowed(permitted_methods=["POST"])
        location = get_object_or_404(
            UserLocation,
            pk=kwargs["user_location"],
            camp__slug=kwargs["camp_slug"],
            user=request.user,
        )
        data = json.loads(request.body)
        if "name" in data:
            location.name = data["name"]
        if "lat" in data and "lon" in data:
            location.location = Point(data["lat"], data["lon"])
        if "data" in data:
            location.data = data["data"]
        location.save()

        return {
            "name": location.name,
            "lat": location.location.x,
            "lon": location.location.y,
            "data": location.data,
        }

    def delete(self, request, **kwargs):
        if "user_location" not in kwargs and "camp_slug" not in kwargs:
            return HttpResponseNotAllowed(permitted_methods=["POST"])
        location = get_object_or_404(
            UserLocation,
            pk=kwargs["user_location"],
            camp__slug=kwargs["camp_slug"],
            user=request.user,
        )
        location.delete()
        return {
            "pk": location.pk,
            "type": location.type.slug,
            "name": location.name,
            "lat": location.location.x,
            "lon": location.location.y,
            "data": location.data,
        }
