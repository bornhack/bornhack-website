import logging

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView
from leaflet.forms.widgets import LeafletWidget

from ..mixins import OrgaTeamPermissionMixin
from ..mixins import RaisePermissionRequiredMixin
from camps.mixins import CampViewMixin
from facilities.models import Facility
from facilities.models import FacilityFeedback
from facilities.models import FacilityOpeningHours
from facilities.models import FacilityType
from teams.models import Team

logger = logging.getLogger("bornhack.%s" % __name__)


class FacilityTypeListView(CampViewMixin, OrgaTeamPermissionMixin, ListView):
    model = FacilityType
    template_name = "facility_type_list_backoffice.html"
    context_object_name = "facility_type_list"


class FacilityTypeCreateView(CampViewMixin, OrgaTeamPermissionMixin, CreateView):
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


class FacilityTypeUpdateView(CampViewMixin, OrgaTeamPermissionMixin, UpdateView):
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


class FacilityTypeDeleteView(CampViewMixin, OrgaTeamPermissionMixin, DeleteView):
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


class FacilityListView(CampViewMixin, OrgaTeamPermissionMixin, ListView):
    model = Facility
    template_name = "facility_list_backoffice.html"


class FacilityDetailView(CampViewMixin, OrgaTeamPermissionMixin, DetailView):
    model = Facility
    template_name = "facility_detail_backoffice.html"
    pk_url_kwarg = "facility_uuid"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.prefetch_related("opening_hours")


class FacilityCreateView(CampViewMixin, OrgaTeamPermissionMixin, CreateView):
    model = Facility
    template_name = "facility_form.html"
    fields = ["facility_type", "name", "description", "location"]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["location"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
            },
        )
        return form

    def get_context_data(self, **kwargs):
        """
        Do not show types that are not part of the current camp in the dropdown
        """
        context = super().get_context_data(**kwargs)
        context["form"].fields["facility_type"].queryset = FacilityType.objects.filter(
            responsible_team__camp=self.camp,
        )
        return context

    def get_success_url(self):
        messages.success(self.request, "The Facility has been created")
        return reverse("backoffice:facility_list", kwargs={"camp_slug": self.camp.slug})


class FacilityUpdateView(CampViewMixin, OrgaTeamPermissionMixin, UpdateView):
    model = Facility
    template_name = "facility_form.html"
    pk_url_kwarg = "facility_uuid"
    fields = ["facility_type", "name", "description", "location"]

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["location"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
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


class FacilityDeleteView(CampViewMixin, OrgaTeamPermissionMixin, DeleteView):
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


class FacilityFeedbackView(CampViewMixin, RaisePermissionRequiredMixin, FormView):
    template_name = "facilityfeedback_backoffice.html"

    def get_permission_required(self):
        """
        This view requires two permissions, camps.backoffice_permission and
        the permission_set for the team in question.
        """
        if not self.team.permission_set:
            raise PermissionDenied("No permissions set defined for this team")
        return ["camps.backoffice_permission", self.team.permission_set]

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


class FacilityMixin(CampViewMixin):
    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.facility = get_object_or_404(Facility, uuid=kwargs["facility_uuid"])

    def get_form(self, *args, **kwargs):
        """
        The default range widgets are a bit shit because they eat the help_text and
        have no indication of which field is for what. So we add a nice placeholder.
        """
        form = super().get_form(*args, **kwargs)
        form.fields["when"].widget.widgets[0].attrs = {
            "placeholder": f"Open Date and Time (YYYY-MM-DD HH:MM). Active time zone is {settings.TIME_ZONE}.",
        }
        form.fields["when"].widget.widgets[1].attrs = {
            "placeholder": f"Close Date and Time (YYYY-MM-DD HH:MM). Active time zone is {settings.TIME_ZONE}.",
        }
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facility"] = self.facility
        return context


class FacilityOpeningHoursCreateView(
    FacilityMixin,
    OrgaTeamPermissionMixin,
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
    FacilityMixin,
    OrgaTeamPermissionMixin,
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
    FacilityMixin,
    OrgaTeamPermissionMixin,
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
