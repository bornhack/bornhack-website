from __future__ import annotations

import json
import logging
import uuid

from django.contrib import messages
from django.contrib.gis.geos import GeometryCollection
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.templatetags.static import static
from django.urls import reverse
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView
from leaflet.forms.widgets import LeafletWidget

from backoffice.forms import MapLayerFeaturesImportForm
from camps.mixins import CampViewMixin
from facilities.models import FacilityType
from maps.mixins import ExternalLayerMapperViewMixin
from maps.mixins import GisTeamViewMixin
from maps.mixins import LayerMapperViewMixin
from maps.models import ExternalLayer
from maps.models import Feature
from maps.models import Layer
from maps.models import UserLocationType
from teams.models import Team
from utils.mixins import AnyTeamMapperRequiredMixin
from utils.widgets import IconPickerWidget

logger = logging.getLogger(f"bornhack.{__name__}")

# ################# Helper ########################


class MapLayerHelper:
    """Helper class to not repeat code in the view classes."""

    camp = None
    request = None

    def __init__(self, camp_slug, request):
        """Class init method."""
        self.camp_slug = camp_slug
        self.request = request

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


# ################# LAYERS ########################


class MapLayerListView(CampViewMixin, AnyTeamMapperRequiredMixin, ListView):
    """View for the list of layers."""

    model = Layer
    template_name = "maps_layer_list_backoffice.html"
    context_object_name = "maps_layer_list"

    def get_context_data(self, **kwargs):
        """Method to get the list of layers."""
        context = super().get_context_data(**kwargs)
        context["layers"] = Layer.objects.filter(
            Q(responsible_team__camp=self.camp) | Q(responsible_team=None),
        )
        context["externalLayers"] = ExternalLayer.objects.filter(
            Q(responsible_team__camp=self.camp) | Q(responsible_team=None),
        )
        return context


class MapLayerFeaturesImportView(
    CampViewMixin,
    LayerMapperViewMixin,
    FormView,
):
    """Import features into a map layer."""

    form_class = MapLayerFeaturesImportForm
    template_name = "maps_layer_import_features_backoffice.html"
    created_count = 0
    updated_count = 0
    error_count = 0

    def form_valid(self, form):
        """Create/update features from the geojson. Show messages and redirect."""
        geojson = form.cleaned_data
        self.load_feature_collection(self.layer, geojson)
        if self.created_count > 0 or self.updated_count > 0:
            messages.success(
                self.request,
                "%i new features created, %i existing features updated" % (self.created_count, self.updated_count),
            )
        if self.error_count > 0:
            messages.error(
                self.request,
                "%i features with errors not imported" % (self.error_count),
            )
        return HttpResponseRedirect(
            reverse(
                "backoffice:map_features_list",
                kwargs={"camp_slug": self.camp.slug, "layer_slug": self.layer.slug},
            ),
        )

    def load_features(self, *features) -> GeometryCollection:
        """Loop over features and return as a GeometryCollection."""
        import_features = []
        for feature in features:
            try:
                f = GEOSGeometry(json.dumps(feature))
                import_features.append(f)
            except (TypeError, AttributeError, ValueError):
                logger.exception(f"Failed to GEOSGeometry: {feature}")
                self.error_count += 1
                return None
        return GeometryCollection(import_features)

    def load_feature_collection(self, layer, geojson) -> None:
        """Loop over the FeatureCollection geojson and process each feature, depending on type."""
        for feature in geojson["features"]:
            if "geometry" not in feature or feature["geometry"] is None:
                # TODO: no geometries in this feature, why do we create a Feature object anyway?
                geom = GeometryCollection([])
            elif feature["geometry"]["type"] == "GeometryCollection":
                # parse GeometryCollection object
                geom = self.load_features(*feature["geometry"]["geometries"])
            elif feature["type"] == "Feature":
                # parse single feature
                geom = self.load_features(feature["geometry"])
            self.create_feature_object(
                feature_uuid=feature.get("id"),
                props=feature["properties"],
                layer=layer,
                geom=geom,
            )

    def create_feature_object(self, feature_uuid, props, layer, geom) -> None:
        """Create or update a Feature object for the given layer with the given geom and props."""
        # do we have an id from the geojson feature?
        if feature_uuid:
            # we have an id in this geojson feature
            try:
                # is it a valid uuid?
                feature_uuid = uuid.UUID(feature_uuid)
                # it is a valid uuid, does it already exist in the db?
                if Feature.objects.exclude(layer=layer).filter(uuid=feature_uuid).exists():
                    feature_uuid = uuid.uuid4()
                # use uuid for lookup
                get_args = {"uuid": feature_uuid}
            except (ValueError, TypeError, AttributeError):
                # not a valid uuid, use name for lookup
                get_args = {"name": props.get("name", "unnamed feature")}
        else:
            get_args = {"name": props.get("name", "unnamed feature")}

        # use layer and uuid/name to select the object
        get_args["layer"] = layer
        try:
            obj, created = Feature.objects.update_or_create(
                **get_args,
                defaults={
                    "layer": layer,
                    "name": props["name"],
                    "description": props["description"],
                    "url": props.get("url", ""),
                    "topic": props.get("topic", ""),
                    "processing": props.get("processing", ""),
                    "color": props.get("color", "#000000FF"),
                    "icon": props.get("icon", "fas fa-list"),
                    "geom": geom,
                },
            )
            if created:
                self.created_count += 1
            else:
                self.updated_count += 1
        except AttributeError:
            self.error_count += 1


class MapLayerCreateView(CampViewMixin, AnyTeamMapperRequiredMixin, CreateView):
    model = Layer
    template_name = "maps_layer_form.html"
    fields = [
        "name",
        "slug",
        "description",
        "icon",
        "invisible",
        "public",
        "group",
        "responsible_team",
    ]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        return form

    def get_context_data(self, **kwargs):
        """Do not show teams that are not part of the current camp in the dropdown."""
        # get the teams the current user has mapper permission for
        perms = self.request.user.get_all_permissions()
        team_slugs = [perm.split(".")[1].split("_")[0] for perm in perms if perm.endswith("_mapper")]
        teams = Team.objects.filter(camp=self.camp, slug__in=team_slugs)
        context = super().get_context_data(**kwargs)
        context["form"].fields["responsible_team"].queryset = teams
        return context

    def get_success_url(self):
        return reverse(
            "backoffice:map_layer_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class MapLayerUpdateView(CampViewMixin, LayerMapperViewMixin, UpdateView):
    model = Layer
    slug_url_kwarg = "layer_slug"
    template_name = "maps_layer_form.html"
    fields = [
        "name",
        "slug",
        "description",
        "icon",
        "invisible",
        "public",
        "group",
        "responsible_team",
    ]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        return form

    def get_context_data(self, **kwargs):
        """Do not show teams that are not part of the current camp in the dropdown."""
        # get the teams the current user has facilitator permission for
        perms = self.request.user.get_all_permissions()
        team_slugs = [perm.split(".")[1].split("_")[0] for perm in perms if perm.endswith("_mapper")]
        teams = Team.objects.filter(camp=self.camp, slug__in=team_slugs)
        context = super().get_context_data(**kwargs)
        context["form"].fields["responsible_team"].queryset = teams
        return context

    def get_success_url(self):
        return reverse(
            "backoffice:map_layer_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class MapLayerDeleteView(CampViewMixin, LayerMapperViewMixin, DeleteView):
    model = Layer
    template_name = "maps_layer_delete.html"
    slug_url_kwarg = "layer_slug"

    def delete(self, *args, **kwargs):
        for layer in self.get_object().features.all():
            layer.delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "The Layer has been deleted")
        return reverse(
            "backoffice:map_layer_list",
            kwargs={"camp_slug": self.camp.slug},
        )


# ################# FEATURES #######################


class MapFeatureListView(LayerMapperViewMixin, ListView):
    model = Feature
    template_name = "maps_layer_feature_list_backoffice.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["features"] = Feature.objects.filter(layer=self.layer)
        return context


class MapFeatureCreateView(LayerMapperViewMixin, CreateView):
    model = Feature
    template_name = "maps_feature_form.html"
    fields = [
        "name",
        "description",
        "url",
        "topic",
        "processing",
        "icon",
        "color",
        "layer",
        "geom",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        helper = MapLayerHelper(self.kwargs["camp_slug"], self.request)
        context.update({"mapData": helper.get_map_data()})
        return context

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        form.fields["layer"].initial = self.layer.pk
        form.fields["layer"].disabled = True
        form.fields["geom"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                "map_height": "500px",
                "geom_type": "GeometryCollection",
                "class": "form-control",
            },
        )
        return form

    def get_success_url(self):
        messages.success(self.request, "The feature has been created")
        return reverse(
            "backoffice:map_features_list",
            kwargs={
                "camp_slug": self.kwargs["camp_slug"],
                "layer_slug": self.layer.slug,
            },
        )


class MapFeatureUpdateView(LayerMapperViewMixin, UpdateView):
    model = Feature
    slug_url_kwarg = "feature_uuid"
    slug_field = "uuid"
    template_name = "maps_feature_form.html"
    fields = [
        "name",
        "description",
        "url",
        "topic",
        "processing",
        "icon",
        "color",
        "geom",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        helper = MapLayerHelper(self.kwargs["camp_slug"], self.request)
        context.update({"mapData": helper.get_map_data()})
        return context

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        form.fields["geom"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                "map_height": "500px",
                "geom_type": "GeometryCollection",
                "class": "form-control",
            },
        )
        return form

    def get_success_url(self):
        messages.success(self.request, "The feature has been updated")
        return reverse(
            "backoffice:map_features_list",
            kwargs={
                "camp_slug": self.kwargs["camp_slug"],
                "layer_slug": self.layer.slug,
            },
        )


class MapFeatureDeleteView(LayerMapperViewMixin, DeleteView):
    model = Feature
    template_name = "maps_feature_delete.html"
    slug_url_kwarg = "feature_uuid"
    slug_field = "uuid"

    def get_success_url(self):
        messages.success(self.request, "The feature has been deleted")
        return reverse(
            "backoffice:map_features_list",
            kwargs={
                "camp_slug": self.kwargs["camp_slug"],
                "layer_slug": self.layer.slug,
            },
        )


# ################# EXTERNAL LAYERS ################


class MapExternalLayerCreateView(CampViewMixin, AnyTeamMapperRequiredMixin, CreateView):
    model = ExternalLayer
    template_name = "maps_external_layer_form.html"
    fields = [
        "name",
        "description",
        "responsible_team",
        "url",
    ]

    def get_context_data(self, **kwargs):
        """Do not show teams that are not part of the current camp in the dropdown."""
        context = super().get_context_data(**kwargs)
        context["form"].fields["responsible_team"].queryset = Team.objects.filter(
            camp=self.camp,
        )
        return context

    def get_success_url(self):
        messages.success(self.request, "The external layer has been created")
        return reverse(
            "backoffice:map_layer_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"]},
        )


class MapExternalLayerUpdateView(ExternalLayerMapperViewMixin, UpdateView):
    model = ExternalLayer
    slug_url_kwarg = "external_layer_uuid"
    slug_field = "uuid"
    template_name = "maps_external_layer_form.html"
    fields = [
        "name",
        "description",
        "responsible_team",
        "url",
    ]

    def get_context_data(self, **kwargs):
        """Do not show teams that are not part of the current camp in the dropdown."""
        context = super().get_context_data(**kwargs)
        context["form"].fields["responsible_team"].queryset = Team.objects.filter(
            camp=self.camp,
        )
        return context

    def get_success_url(self):
        messages.success(self.request, "The external layer has been updated")
        return reverse(
            "backoffice:map_layer_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"]},
        )


class MapExternalLayerDeleteView(ExternalLayerMapperViewMixin, DeleteView):
    model = ExternalLayer
    template_name = "maps_external_layer_delete.html"
    slug_url_kwarg = "external_layer_uuid"
    slug_field = "uuid"
    context_object_name = "external_layer"

    def get_success_url(self):
        messages.success(self.request, "The external layer has been deleted")
        return reverse(
            "backoffice:map_layer_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"]},
        )


# ################# User Location Types ############


class MapUserLocationTypeListView(GisTeamViewMixin, ListView):
    model = UserLocationType
    template_name = "maps_user_location_type_list.html"


class MapUserLocationTypeCreateView(GisTeamViewMixin, CreateView):
    model = UserLocationType
    template_name = "maps_user_location_type_form.html"
    fields = [
        "name",
        "slug",
        "icon",
        "marker",
    ]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        return form

    def get_success_url(self):
        messages.success(self.request, "The User Location Type has been created")
        return reverse(
            "backoffice:map_user_location_type_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"]},
        )


class MapUserLocationTypeUpdateView(GisTeamViewMixin, UpdateView):
    model = UserLocationType
    template_name = "maps_user_location_type_form.html"
    slug_url_kwarg = "user_location_type_uuid"
    slug_field = "pk"
    fields = [
        "name",
        "slug",
        "icon",
        "marker",
    ]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        return form

    def get_success_url(self):
        messages.success(self.request, "The User Location Type has been updated")
        return reverse(
            "backoffice:map_user_location_type_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"]},
        )


class MapUserLocationTypeDeleteView(GisTeamViewMixin, DeleteView):
    model = UserLocationType
    template_name = "maps_user_location_type_delete.html"
    slug_url_kwarg = "user_location_type_uuid"
    slug_field = "pk"
    context_object_name = "user_location_type"

    def get_success_url(self):
        messages.success(self.request, "The User Location Type has been deleted")
        return reverse(
            "backoffice:map_user_location_type_list",
            kwargs={"camp_slug": self.kwargs["camp_slug"]},
        )
