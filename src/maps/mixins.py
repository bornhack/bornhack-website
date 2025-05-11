from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import get_object_or_404

from .models import Layer
from .models import ExternalLayer
from camps.mixins import CampViewMixin


class LayerViewMixin:
    """A mixin to get the Layer object based on layer_slug in url kwargs."""

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.layer = get_object_or_404(Layer, slug=self.kwargs["layer_slug"])

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["layer"] = self.layer
        return context


class LayerMapperViewMixin(LayerViewMixin):
    """A mixin for views only available to users with mapper permission for the team responsible for the layer and/or Mapper team permission."""

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if (
            self.layer.responsible_team
            and self.layer.responsible_team.mapper_permission_set
            in request.user.get_all_permissions()
        ) or self.request.user.has_perm("camps.gis_team_member"):
            return
        else:
            messages.error(request, "No thanks")
            raise PermissionDenied()


class GisTeamViewMixin:
    """A mixin for views only available to users with `camps.gis_team_member` permission."""

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if self.request.user.has_perm("camps.gis_team_member"):
            return
        else:
            messages.error(request, "No thanks")
            raise PermissionDenied()


class ExternalLayerViewMixin(CampViewMixin):
    """A mixin to get the ExternalLayer object based on external_layer_uuid in url kwargs."""

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.layer = get_object_or_404(
            ExternalLayer,
            slug=self.kwargs["external_layer_uuid"],
        )


class ExternalLayerMapperViewMixin(ExternalLayerViewMixin):
    """A mixin for views only available to users with mapper permission for the team responsible for the layer and/or Mapper team permission."""

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if (
            self.layer.responsible_team
            and self.layer.responsible_team.mapper_permission_set
            in request.user.get_all_permissions()
        ) or self.request.user.has_perm("camps.gis_team_member"):
            return
        else:
            messages.error(request, "No thanks")
            raise PermissionDenied()
