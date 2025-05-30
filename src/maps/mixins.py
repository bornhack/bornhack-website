"""Mixins for Maps app."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from camps.mixins import CampViewMixin

from .models import ExternalLayer
from .models import Layer


class LayerViewMixin:
    """A mixin to get the Layer object based on layer_slug in url kwargs."""

    def setup(self, *args, **kwargs) -> None:
        """Set self.layer based on layer_slug in url kwargs."""
        super().setup(*args, **kwargs)
        self.layer = get_object_or_404(Layer, slug=self.kwargs["layer_slug"])
        if not self.layer.public:
            if ((self.layer.responsible_team and
            self.layer.responsible_team.member_permission_set in self.request.user.get_all_permissions()) or
            self.request.user.has_perm("camps.gis_team_member")):
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
