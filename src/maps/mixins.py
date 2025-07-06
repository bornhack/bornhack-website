"""Mixins for Maps app."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.urls import reverse

from camps.mixins import CampViewMixin
from facilities.models import FacilityType

from .models import ExternalLayer
from .models import Layer


class LayerViewMixin:
    """A mixin to get the Layer object based on layer_slug in url kwargs."""

    def setup(self, *args, **kwargs) -> None:
        """Set self.layer based on layer_slug in url kwargs."""
        super().setup(*args, **kwargs)
        self.layer = get_object_or_404(Layer, slug=self.kwargs["layer_slug"])
        if not self.layer.public:
            if (
                self.layer.responsible_team
                and self.layer.responsible_team.member_permission_set in self.request.user.get_all_permissions()
            ) or self.request.user.has_perm("camps.gis_team_member"):
                return
            raise PermissionDenied

    def get_context_data(self, *args, **kwargs) -> dict:
        """Add self.layer to context."""
        context = super().get_context_data(*args, **kwargs)
        context["layer"] = self.layer
        return context


class LayerMapperViewMixin(LayerViewMixin):
    """A mixin for LayerMapper.

    For views only available to users with mapper permission for the team responsible
    for the layer and/or Mapper team permission.
    """

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """Check permissions."""
        super().setup(request, *args, **kwargs)
        if (
            self.layer.responsible_team
            and self.layer.responsible_team.mapper_permission_set in request.user.get_all_permissions()
        ) or self.request.user.has_perm("camps.gis_team_member"):
            return
        messages.error(request, "No thanks")
        raise PermissionDenied


class GisTeamViewMixin:
    """A mixin for views only available to users with `camps.gis_team_member` permission."""

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """Check permissions."""
        super().setup(request, *args, **kwargs)
        if self.request.user.has_perm("camps.gis_team_member"):
            return
        messages.error(request, "No thanks")
        raise PermissionDenied


class ExternalLayerViewMixin(CampViewMixin):
    """A mixin to get the ExternalLayer object based on external_layer_uuid in url kwargs."""

    def setup(self, *args, **kwargs) -> None:
        """Set self.layer."""
        super().setup(*args, **kwargs)
        self.layer = get_object_or_404(
            ExternalLayer,
            slug=self.kwargs["external_layer_uuid"],
        )


class ExternalLayerMapperViewMixin(ExternalLayerViewMixin):
    """A mixin for views.

    only available to users with mapper permission for the team responsible
    for the layer and/or Mapper team permission.
    """

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """Check permissions."""
        super().setup(request, *args, **kwargs)
        if (
            self.layer.responsible_team
            and self.layer.responsible_team.mapper_permission_set in request.user.get_all_permissions()
        ) or self.request.user.has_perm("camps.gis_team_member"):
            return
        messages.error(request, "No thanks")
        raise PermissionDenied


class LayerMapMixin:
    """Mixin for loading the map data from the layers."""

    camp_slug = None

    def setup(self, request: HttpRequest, *args, **kwargs) -> None:
        """Class init method."""
        super().setup(request, *args, **kwargs)
        self.camp_slug = kwargs["camp_slug"]

    def get_layers(self) -> QuerySet:
        """Method to get the layers the user has access to."""
        user_teams = []
        if not self.request.user.is_anonymous:
            user_teams = self.request.user.teammember_set.filter(
                team__camp__slug=self.camp_slug,
            ).values_list("team__name", flat=True)
        return Layer.objects.filter(
            ((Q(responsible_team__camp__slug=self.camp_slug) | Q(responsible_team=None)) & Q(public=True))
            | (Q(responsible_team__name__in=user_teams) & Q(public=False)),
        )

    def get_map_data(self) -> dict:
        """Method to return the map_data."""
        map_data = {
            "grid": static("json/grid.geojson"),
            "loggedIn": self.request.user.is_authenticated,
            "layers": [],
            "facilitytype_list": [],
        }
        facilitytype_list = FacilityType.objects.filter(
            responsible_team__camp__slug=self.camp_slug,
        )
        map_data.update({"facilitytype_list": list(facilitytype_list.values())})
        layers = self.get_layers()
        map_data.update(
            {
                "layers": list(
                    layers.values(
                        "description",
                        "name",
                        "slug",
                        "uuid",
                        "icon",
                        "invisible",
                        "group__name",
                    ),
                ),
            },
        )
        for facility in map_data["facilitytype_list"]:
            facility["url"] = reverse(
                "facilities:facility_list_geojson",
                kwargs={
                    "camp_slug": self.camp_slug,
                    "facility_type_slug": facility["slug"],
                },
            )
        for layer in map_data["layers"]:
            layer["url"] = reverse(
                "maps:map_layer_geojson",
                kwargs={"layer_slug": layer["slug"]},
            )
        return map_data
