"""Maps view."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.core.exceptions import BadRequest
from django.core.exceptions import PermissionDenied
from django.core.serializers import serialize
from django.db.models import Q
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic import View
from django.views.generic.base import TemplateView
from jsonview.views import JsonView
from leaflet.forms.widgets import LeafletWidget
from oauth2_provider.views.generic import ScopedProtectedResourceView

if TYPE_CHECKING:
    from uuid import UUID

    from django.db.models import QuerySet
    from django.forms import BaseForm
    from django.template.response import TemplateResponse

from typing import ClassVar

from camps.mixins import CampViewMixin
from facilities.models import FacilityType
from utils.color import adjust_color
from utils.color import is_dark
from utils.mixins import UserIsObjectOwnerMixin

from .mixins import LayerViewMixin
from .models import ExternalLayer
from .models import Feature
from .models import Layer
from .models import UserLocation
from .models import UserLocationType

logger = logging.getLogger(f"bornhack.{__name__}")


class MissingCredentialsError(Exception):
    """Missing Credentials Exception."""


class MarkerColorError(ValueError):
    """Exception raised on invalid color."""

    def __init__(self) -> None:
        """Exception raised on invalid color."""
        error = "Hex color must be in format RRGGBB or RRGGBBAA"
        logger.exception(error)
        super().__init__(error)


class MapMarkerView(TemplateView):
    """View for generating the coloured marker."""

    template_name = "marker.svg"

    @property
    def color(self) -> tuple[int, int, int] | tuple[int, int, int, int]:
        """Return the color values as ints."""
        hex_color = self.kwargs["color"]
        length = len(hex_color)

        if length == 6:  # RGB # noqa: PLR2004
            try:
                r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
            except ValueError as e:
                raise MarkerColorError from e
            return (r, g, b)
        if length == 8:  # RGBA # noqa: PLR2004
            try:
                r, g, b, a = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4, 6))
            except ValueError as e:
                raise MarkerColorError from e
            return (r, g, b, a)
        raise MarkerColorError

    def get_context_data(self, **kwargs) -> dict[str, tuple[int, int, int] | tuple[int, int, int, int]]:
        """Get the context data."""
        context = super().get_context_data(**kwargs)
        try:
            context["stroke0"] = adjust_color(self.color, -0.4) if is_dark(self.color) else adjust_color(self.color)
            context["stroke1"] = self.color
            context["fill0"] = adjust_color(self.color, -0.4) if is_dark(self.color) else adjust_color(self.color)
            context["fill1"] = self.color
        except MarkerColorError as e:
            raise BadRequest from e
        return context

    def render_to_response(self, context: dict, **kwargs) -> TemplateResponse:
        """Render the SVG output."""
        return super().render_to_response(
            context,
            content_type="image/svg+xml",
            **kwargs,
        )


class LayerJsonView(JsonView):
    """View for returning all available layers in json."""

    def get_context_data(self, **kwargs) -> list:
        """Return the GeoJSON Data to the client."""
        layers = []
        for layer in Layer.objects.filter(public=True):
            url = reverse(
                "maps:map_layer_geojson",
                kwargs={"layer_slug": layer.slug},
            )
            layers.append(
                {
                    "name": layer.name,
                    "team": layer.responsible_team.name if layer.responsible_team else "None",
                    "camp": layer.responsible_team.camp.slug if layer.responsible_team else "all",
                    "url": self.request.build_absolute_uri(url),
                },
            )
        for facility_type in FacilityType.objects.all():
            url = reverse(
                "facilities:facility_list_geojson",
                kwargs={
                    "camp_slug": facility_type.responsible_team.camp.slug,
                    "facility_type_slug": facility_type.slug,
                },
            )
            layers.append(
                {
                    "name": facility_type.name,
                    "team": facility_type.responsible_team.name,
                    "camp": facility_type.responsible_team.camp.slug,
                    "url": self.request.build_absolute_uri(url),
                },
            )

        return layers


class MapView(CampViewMixin, TemplateView):
    """Global map view."""

    template_name = "maps_map.html"
    context_object_name = "maps_map"

    def get_layers(self) -> QuerySet:
        """Method to get the layers the user has access to."""
        user_teams = []
        if not self.request.user.is_anonymous:
            user_teams = self.request.user.teammember_set.filter(
                team__camp=self.camp,
            ).values_list("team__name", flat=True)
        return Layer.objects.filter(
            ((Q(responsible_team__camp=self.camp) | Q(responsible_team=None)) & Q(public=True))
            | (Q(responsible_team__name__in=user_teams) & Q(public=False)),
        )

    def get_context_data(self, **kwargs) -> dict:
        """Get the context data."""
        context = super().get_context_data(**kwargs)
        context["facilitytype_list"] = FacilityType.objects.filter(
            responsible_team__camp=self.camp,
        )
        context["layers"] = self.get_layers()
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
                "villages:villages_geojson",
                kwargs={"camp_slug": self.camp.slug},
            ),
            "user_location_types": list(
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
        for user_location_type in context["mapData"]["user_location_types"]:
            user_location_type["url"] = reverse(
                "maps_user_location_layer",
                kwargs={
                    "user_location_type_slug": user_location_type["slug"],
                    "camp_slug": self.camp.slug,
                },
            )
        return context


class LayerGeoJSONView(LayerViewMixin, JsonView):
    """GeoJSON export view."""

    def get_context_data(self, **kwargs) -> dict:
        """Return the GeoJSON Data to the client."""
        return json.loads(
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


@method_decorator(cache_control(public=True), name="dispatch")
@method_decorator(cache_page(86400), name="dispatch")
class MapProxyView(View):
    """Proxy for Datafordeler map service.

    Created so we can show maps without leaking the IP of our visitors.
    """

    PROXY_URL = "/maps/kfproxy"
    VALID_ENDPOINTS: ClassVar[list[str]] = [
        "/GeoDanmarkOrto/orto_foraar_wmts/1.0.0/WMTS",
        "/GeoDanmarkOrto/orto_foraar/1.0.0/WMS",
        "/Dkskaermkort/topo_skaermkort/1.0.0/wms",
        "/DHMNedboer/dhm/1.0.0/wms",
    ]

    def get(self, *args, **kwargs) -> HttpResponse:
        """Before we make the request we check that the path is in our whitelist.

        Before we return the response we copy headers except for a list we dont want.
        """
        # Raise PermissionDenied if endpoint isn't valid
        self.is_endpoint_valid(self.request.path)

        # Sanitize the query
        path = self.sanitize_path(self.request.get_full_path())

        # Add credentials to query
        path = self.append_credentials(path)

        # make the request
        r = requests.get("https://services.datafordeler.dk" + path, timeout=10)

        # make the response
        response = HttpResponse(r.content, status=r.status_code)

        # list of headers that cause trouble when proxying
        excluded_headers = [
            "cache-control",
            "connection",
            "content-encoding",
            "content-length",
            "expires",
            "keep-alive",
            "pragma",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
            "vary",
        ]
        # proxy all headers from our upstream request to the response to our client,
        # if the headers are not in our list of troublemakers
        for key, value in r.headers.items():
            if key.lower() not in excluded_headers:
                response[key] = value

        # all good, return the response
        return response

    def is_endpoint_valid(self, path: str) -> None:
        """Validate request path against whitelisted endpoints or raise PermDenied."""
        endpoint = path.replace(self.PROXY_URL, "", 1)
        if endpoint not in self.VALID_ENDPOINTS:
            logger.warning(
                "Maps endpoint was invalid: '%s' valid endpoints: %s",
                endpoint,
                self.VALID_ENDPOINTS,
            )
            raise PermissionDenied

    def sanitize_path(self, path: str) -> str:
        """Sanitize path by removing PROXY_URL and set 'transparent' value to upper."""
        new_path = path.replace(self.PROXY_URL, "", 1)
        return re.sub(
            r"(transparent=)(true|false)",
            lambda match: rf"{match.group(1)}{match.group(2).upper()}",
            new_path,
        )

    def append_credentials(self, path: str) -> str:
        """Verify credentials are defined in settings & append or raise exception."""
        username = settings.DATAFORDELER_USER
        password = settings.DATAFORDELER_PASSWORD
        if not username or not password:
            logger.error(
                "Missing credentials for 'DATAFORDELER_USER' or 'DATAFORDELER_PASSWORD'",
            )
            raise MissingCredentialsError
        path += f"&username={username}&password={password}"
        return path


# User Location views


class UserLocationLayerView(CampViewMixin, JsonView):
    """UserLocation geojson view."""

    def get_context_data(self, **kwargs) -> dict:
        """Get context data."""
        context = {}
        context["type"] = "FeatureCollection"
        context["features"] = self.dump_locations()
        return context

    def dump_locations(self) -> list[object]:
        """GeoJSON Formatter."""
        return [
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
            }
            for location in UserLocation.objects.filter(
                camp=self.camp,
                type__slug=self.kwargs["user_location_type_slug"],
            )
        ]


class UserLocationListView(LoginRequiredMixin, CampViewMixin, ListView):
    """UserLocation view."""

    template_name = "user_location_list.html"
    model = UserLocation

    def get_context_data(self, **kwargs) -> dict:
        """Get data for the view."""
        context = super().get_context_data(**kwargs)
        context["user_location_types"] = UserLocationType.objects.all().values_list(
            "slug",
            flat=True,
        )
        return context

    def get_queryset(self, *args, **kwargs) -> QuerySet:
        """Show only entries belonging to the current user."""
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(user=self.request.user)


class UserLocationCreateView(LoginRequiredMixin, CampViewMixin, CreateView):
    """Create view for UserLocation."""

    model = UserLocation
    template_name = "user_location_form.html"
    fields: ClassVar[list[str]] = ["name", "type", "location", "data"]

    def dispatch(self, *args, **kwargs) -> str:
        """Check user limits."""
        if (
            UserLocation.objects.filter(user=self.request.user, camp=self.camp).count()
            >= settings.MAPS_USER_LOCATION_MAX
        ):
            messages.error(
                self.request,
                "To many User Locations (50), please delete some.",
            )
            return redirect(
                reverse(
                    "maps_user_location_list",
                    kwargs={"camp_slug": self.camp.slug},
                ),
            )
        return super().dispatch(*args, **kwargs)

    def get_form(self, *args, **kwargs) -> BaseForm:
        """Prepare the form."""
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

    def form_valid(self, form: BaseForm) -> str:
        """Check if the form is valid."""
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
    """Update view for UserLocation."""

    model = UserLocation
    template_name = "user_location_form.html"
    fields: ClassVar[list[str]] = ["name", "type", "location", "data"]
    slug_url_kwarg = "user_location"
    slug_field = "pk"

    def get_context_data(self, **kwargs) -> dict:
        """Get the context data for the view."""
        context = super().get_context_data(**kwargs)
        context["mapData"] = {"grid": static("json/grid.geojson")}
        return context

    def get_form(self, *args, **kwargs) -> BaseForm:
        """get_form preparing the form."""
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

    def get_success_url(self) -> str:
        """Produce the success url."""
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
    """Delete view for UserLocation."""

    model = UserLocation
    template_name = "user_location_delete.html"
    slug_url_kwarg = "user_location"
    slug_field = "pk"

    def get_success_url(self) -> str:
        """Produce the success url."""
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
    """This view has 2 endpoints /create/api (POST) AND /<uuid>/api (GET, PATCH, DELETE)."""

    required_scopes: ClassVar[list[str]] = ["location:write"]

    def get(self, request: HttpRequest, **kwargs) -> dict:
        """HTTP Method for viewing a user location."""
        if "user_location" not in kwargs:
            return HttpResponseNotAllowed(permitted_methods=["POST"])
        location = get_object_or_404(
            UserLocation,
            pk=kwargs["user_location"],
        )
        return {
            "uuid": location.pk,
            "type": location.type.slug,
            "name": location.name,
            "lat": location.location.x,
            "lon": location.location.y,
            "data": location.data,
        }

    def post(self, request: HttpRequest, **kwargs) -> dict:
        """HTTP Method for creating a user location."""
        if "user_location" in kwargs:
            return HttpResponseNotAllowed(permitted_methods=["GET", "PATCH", "DELETE"])
        if UserLocation.objects.filter(user=request.user, camp=self.camp).count() >= settings.MAPS_USER_LOCATION_MAX:
            return {"error": "To many user locations created (50)"}
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
            "uuid": location.pk,
            "type": location.type.slug,
            "name": location.name,
            "lat": location.location.x,
            "lon": location.location.y,
            "data": location.data,
        }

    def patch(
        self,
        request: HttpRequest,
        **kwargs,
    ) -> dict[str, str | int | float | UUID] | HttpResponseNotAllowed | tuple[dict[str, str], int]:
        """HTTP Method for updating a user location."""
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
        if "type" in data:
            try:
                location.type = UserLocationType.objects.get(slug=data["type"])
            except UserLocationType.DoesNotExist:
                return {"error": "Type not found"}, 404
        location.save()

        return {
            "uuid": location.pk,
            "type": location.type.slug,
            "name": location.name,
            "lat": location.location.x,
            "lon": location.location.y,
            "data": location.data,
        }

    def delete(self, request: HttpRequest, **kwargs) -> HttpResponse | HttpResponseNotAllowed:
        """HTTP Method for deleting a user location."""
        if "user_location" not in kwargs and "camp_slug" not in kwargs:
            return HttpResponseNotAllowed(permitted_methods=["POST"])
        location = get_object_or_404(
            UserLocation,
            pk=kwargs["user_location"],
            camp__slug=kwargs["camp_slug"],
            user=request.user,
        )
        location.delete()
        return HttpResponse(status_code=204)
