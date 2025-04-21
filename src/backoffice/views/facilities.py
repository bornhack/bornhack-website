import json
import logging

from django.contrib import messages
from django.contrib.gis.geos import GEOSGeometry
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.base import View
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView
from leaflet.forms.widgets import LeafletWidget

from ..mixins import OrgaOrGisTeamViewMixin
from ..mixins import RaisePermissionRequiredMixin
from facilities.mixins import FacilityFacilitatorViewMixin
from camps.mixins import CampViewMixin
from facilities.models import Facility
from facilities.models import FacilityFeedback
from facilities.models import FacilityOpeningHours
from facilities.models import FacilityType
from teams.models import Team
from utils.widgets import IconPickerWidget
from utils.mixins import AnyTeamFacilitatorRequiredMixin

logger = logging.getLogger("bornhack.%s" % __name__)


# ########### FACILITY TYPES ######################


class FacilityTypeListView(CampViewMixin, OrgaOrGisTeamViewMixin, ListView):
    model = FacilityType
    template_name = "facility_type_list_backoffice.html"
    context_object_name = "facility_type_list"


class FacilityTypeImportView(CampViewMixin, OrgaOrGisTeamViewMixin, View):
    model = FacilityType
    template_name = "facility_type_import_backoffice.html"
    context_object_name = "facility_type_import"

    def get(self, request, *args, **kwargs):
        return render(request, "facility_type_import_backoffice.html")

    def post(self, request, camp_slug, slug):
        geojson_data = request.POST.get("geojson_data")
        facility_type = get_object_or_404(
            FacilityType,
            responsible_team__camp=self.camp,
            slug=slug,
        )
        try:
            geojson = json.loads(geojson_data)
        except json.JSONDecodeError:
            return render(
                request,
                "facility_type_import_backoffice.html",
                {"error": "Invalid GeoJSON data"},
            )

        # Basic validation, you can add more checks
        if "type" not in geojson or geojson["type"] != "FeatureCollection":
            return render(
                request,
                "facility_type_import_backoffice.html",
                {"error": "Invalid GeoJSON format"},
            )

        createdCount = 0
        updateCount = 0
        errorCount = 0
        for feature in geojson["features"]:
            try:
                geom = GEOSGeometry(json.dumps(feature["geometry"]))
            except (TypeError, AttributeError):
                errorCount += 1
                continue
            props = feature["properties"]
            if "description" in props:
                if props["description"]:
                    description = props["description"]
                else:
                    errorCount += 1
                    continue
            else:
                errorCount += 1
                continue
            obj, created = Facility.objects.update_or_create(
                name=props["name"],
                description=description,
                facility_type=facility_type,
                location=geom,
            )
            if created:
                createdCount += 1
            else:
                updateCount += 1
        if createdCount > 0 or updateCount > 0:
            messages.success(
                self.request,
                "%i features created, %i features updated"
                % (createdCount, updateCount),
            )
        if errorCount > 0:
            messages.error(
                self.request,
                "%i features with errors not imported" % (errorCount),
            )
        return HttpResponseRedirect(
            reverse(
                "backoffice:facility_type_list",
                kwargs={"camp_slug": camp_slug},
            ),
        )


class FacilityTypeCreateView(CampViewMixin, OrgaOrGisTeamViewMixin, CreateView):
    model = FacilityType
    template_name = "facility_type_form.html"
    fields = [
        "name",
        "description",
        "icon",
        "marker",
        "responsible_team",
        "quickfeedback_options",
    ]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        return form

    def get_context_data(self, **kwargs):
        """
        Do not show teams that are not part of the current camp in the dropdown
        """
        context = super().get_context_data(**kwargs)
        context["form"].fields["responsible_team"].queryset = Team.objects.filter(
            camp=self.camp,
        )
        return context

    def get_success_url(self):
        return reverse(
            "backoffice:facility_type_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class FacilityTypeUpdateView(CampViewMixin, OrgaOrGisTeamViewMixin, UpdateView):
    model = FacilityType
    template_name = "facility_type_form.html"
    fields = [
        "name",
        "description",
        "icon",
        "marker",
        "responsible_team",
        "quickfeedback_options",
    ]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["icon"].widget = IconPickerWidget()
        return form

    def get_context_data(self, **kwargs):
        """
        Do not show teams that are not part of the current camp in the dropdown
        """
        context = super().get_context_data(**kwargs)
        context["form"].fields["responsible_team"].queryset = Team.objects.filter(
            camp=self.camp,
        )
        return context

    def get_success_url(self):
        return reverse(
            "backoffice:facility_type_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class FacilityTypeDeleteView(CampViewMixin, OrgaOrGisTeamViewMixin, DeleteView):
    model = FacilityType
    template_name = "facility_type_delete.html"
    context_object_name = "facility_type"

    def delete(self, *args, **kwargs):
        for facility in self.get_object().facilities.all():
            facility.feedbacks.all().delete()
            facility.opening_hours.all().delete()
            facility.delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "The FacilityType has been deleted")
        return reverse(
            "backoffice:facility_type_list",
            kwargs={"camp_slug": self.camp.slug},
        )


# ########### FACILITIES ######################


class FacilityListView(CampViewMixin, AnyTeamFacilitatorRequiredMixin, ListView):
    model = Facility
    template_name = "facility_list_backoffice.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "loggedIn": self.request.user.is_authenticated,
            "grid": static("json/grid.geojson"),
            "facility_list": [],
        }
        for item in context["facility_list"]:
            context["mapData"]["facility_list"].append(
                {
                    "url": reverse(
                        "backoffice:facility_detail",
                        kwargs={
                            "camp_slug": item.camp.slug,
                            "facility_uuid": item.uuid,
                        },
                    ),
                    "name": item.name,
                    "description": item.description,
                    "location": {
                        "x": item.location.x,
                        "y": item.location.y,
                    },
                    "facility_type": {
                        "icon": item.facility_type.icon,
                        "marker": item.facility_type.marker,
                        "team": item.facility_type.responsible_team.name,
                    },
                },
            )
        return context


class FacilityDetailView(AnyTeamFacilitatorRequiredMixin, DetailView):
    model = Facility
    template_name = "facility_detail_backoffice.html"
    pk_url_kwarg = "facility_uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "loggedIn": self.request.user.is_authenticated,
            "facility": {
                "location": {
                    "x": context["facility"].location.x,
                    "y": context["facility"].location.y,
                },
                "name": context["facility"].name,
                "facility_type": {
                    "marker": context["facility"].facility_type.marker,
                    "icon": context["facility"].facility_type.icon,
                },
                "description": context["facility"].description,
            },
            "grid": static("json/grid.geojson"),
        }
        return context

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.prefetch_related("opening_hours")


class FacilityCreateView(CampViewMixin, AnyTeamFacilitatorRequiredMixin, CreateView):
    model = Facility
    template_name = "facility_form.html"
    fields = ["facility_type", "name", "description", "location"]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["location"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                "class": "form-control",
            },
        )
        return form

    def get_context_data(self, **kwargs):
        """
        Do not show types that are not part of the current camp in the dropdown,
        also hide types belonging to teams for which the user has no facilitator permission.
        Also get map data.
        """
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "loggedIn": True,
            "grid": static("json/grid.geojson"),
        }
        # get the teams the current user has facilitator permission for
        perms = self.request.user.get_all_permissions()
        team_slugs = [
            perm.split(".")[1].split("_")[0]
            for perm in perms
            if perm.endswith("_facilitator")
        ]
        teams = Team.objects.filter(camp=self.camp, slug__in=team_slugs)
        context["form"].fields["facility_type"].queryset = FacilityType.objects.filter(
            responsible_team__camp=self.camp,
            responsible_team__in=teams,
        )
        return context

    def form_valid(self, form):
        # does the user have facilitator permission for the team in charge of this facility type?
        if (
            form.cleaned_data[
                "facility_type"
            ].responsible_team.facilitator_permission_set
            not in self.request.user.get_all_permissions()
        ):
            messages.error("No thanks")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "The Facility has been created")
        return reverse("backoffice:facility_list", kwargs={"camp_slug": self.camp.slug})


class FacilityUpdateView(FacilityFacilitatorViewMixin, UpdateView):
    """Update a facility. Requires facilitator permission for the team which is responsible for the facility type."""

    model = Facility
    template_name = "facility_form.html"
    pk_url_kwarg = "facility_uuid"
    fields = ["name", "description", "location"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "loggedIn": self.request.user.is_authenticated,
            "grid": static("json/grid.geojson"),
        }
        return context

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["location"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                "map_height": "500px",
                "class": "form-control",
            },
        )
        return form

    def get_success_url(self):
        messages.success(self.request, "The Facility has been updated")
        return reverse(
            "backoffice:facility_detail",
            kwargs={
                "camp_slug": self.camp.slug,
                "facility_uuid": self.get_object().uuid,
            },
        )


class FacilityDeleteView(FacilityFacilitatorViewMixin, DeleteView):
    """Delete a facility. Requires facilitator permission for the team which is responsible for the facility type."""

    model = Facility
    template_name = "facility_delete.html"
    pk_url_kwarg = "facility_uuid"

    def delete(self, *args, **kwargs):
        self.get_object().feedbacks.all().delete()
        self.get_object().opening_hours.all().delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "The Facility has been deleted")
        return reverse("backoffice:facility_list", kwargs={"camp_slug": self.camp.slug})


# ############ FACILITY FEEDBACK #####################


class FacilityFeedbackView(CampViewMixin, RaisePermissionRequiredMixin, FormView):
    """View to handle facility feedback. Available for anyone with member permission for the team."""

    template_name = "facilityfeedback_backoffice.html"

    def get_permission_required(self):
        """
        This view requires the member_permission_set for the team in question.
        """
        return [self.team.member_permission_set]

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.team = get_object_or_404(
            Team,
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        self.queryset = FacilityFeedback.objects.filter(
            facility__facility_type__responsible_team=self.team,
            handled=False,
        )
        self.form_class = modelformset_factory(
            FacilityFeedback,
            fields=("handled",),
            min_num=self.queryset.count(),
            validate_min=True,
            max_num=self.queryset.count(),
            validate_max=True,
            extra=0,
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["team"] = self.team
        context["feedback_list"] = self.queryset
        context["formset"] = self.form_class(queryset=self.queryset)
        return context

    def form_valid(self, form):
        form.save()
        if form.changed_objects:
            messages.success(
                self.request,
                f"Marked {len(form.changed_objects)} FacilityFeedbacks as handled!",
            )
        return redirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        return reverse(
            "backoffice:facilityfeedback",
            kwargs={"camp_slug": self.camp.slug, "team_slug": self.team.slug},
        )


# ############ FACILITY OPENING HOURS #####################


class FacilityOpeningHoursCreateView(
    FacilityFacilitatorViewMixin,
    CreateView,
):
    model = FacilityOpeningHours
    template_name = "facility_opening_hours_form.html"
    fields = ["when", "notes"]

    def form_valid(self, form):
        """
        Set facility before saving
        """
        hours = form.save(commit=False)
        hours.facility = self.facility
        hours.save()
        messages.success(self.request, "New opening hours created successfully!")
        return redirect(
            reverse(
                "backoffice:facility_detail",
                kwargs={"camp_slug": self.camp.slug, "facility_uuid": self.facility.pk},
            ),
        )


class FacilityOpeningHoursUpdateView(
    FacilityFacilitatorViewMixin,
    UpdateView,
):
    model = FacilityOpeningHours
    template_name = "facility_opening_hours_form.html"
    fields = ["when", "notes"]

    def get_success_url(self):
        messages.success(self.request, "Opening hours have been updated successfully")
        return reverse(
            "backoffice:facility_detail",
            kwargs={"camp_slug": self.camp.slug, "facility_uuid": self.facility.pk},
        )


class FacilityOpeningHoursDeleteView(
    FacilityFacilitatorViewMixin,
    DeleteView,
):
    model = FacilityOpeningHours
    template_name = "facility_opening_hours_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Opening hours have been deleted successfully")
        return reverse(
            "backoffice:facility_detail",
            kwargs={"camp_slug": self.camp.slug, "facility_uuid": self.facility.pk},
        )
