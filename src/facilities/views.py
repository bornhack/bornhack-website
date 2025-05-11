from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from jsonview.views import JsonView

from camps.mixins import CampViewMixin

from .mixins import FacilityTypeViewMixin
from .mixins import FacilityViewMixin
from .models import Facility
from .models import FacilityFeedback
from .models import FacilityType


class FacilityTypeListView(CampViewMixin, ListView):
    model = FacilityType
    template_name = "facility_type_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "loggedIn": self.request.user.is_authenticated,
            "grid": static("json/grid.geojson"),
            "facilitytypeList": list(context["facilitytype_list"].values()),
        }
        for facility in context["mapData"]["facilitytypeList"]:
            facility["url"] = reverse(
                "facilities:facility_list_geojson",
                kwargs={
                    "camp_slug": self.camp.slug,
                    "facility_type_slug": facility["slug"],
                },
            )
        return context


class FacilityListGeoJSONView(CampViewMixin, JsonView):
    def get_context_data(self, **kwargs):
        return {"type": "FeatureCollection", "features": self.dump_features()}

    def dump_features(self) -> list[object]:
        output = []
        for ft in FacilityType.objects.filter(
            responsible_team__camp=self.camp,
            slug=self.kwargs["facility_type_slug"],
        ):
            for facility in Facility.objects.filter(facility_type=ft.pk):
                entry = {
                    "type": "Feature",
                    "id": facility.pk,
                    "geometry": {
                        "type": "Point",
                        "coordinates": [facility.location.x, facility.location.y],
                    },
                    "properties": {
                        "name": facility.name,
                        "marker": facility.facility_type.marker,
                        "icon": facility.facility_type.icon,
                        "description": facility.description,
                        "team": facility.facility_type.responsible_team.name,
                        "uuid": facility.uuid,
                        "type": ft.name,
                        "detail_url": reverse(
                            "facilities:facility_detail",
                            kwargs={
                                "camp_slug": facility.camp.slug,
                                "facility_type_slug": facility.facility_type.slug,
                                "facility_uuid": facility.uuid,
                            },
                        ),
                        "feedback_url": reverse(
                            "facilities:facility_feedback",
                            kwargs={
                                "camp_slug": facility.camp.slug,
                                "facility_type_slug": facility.facility_type.slug,
                                "facility_uuid": facility.uuid,
                            },
                        ),
                    },
                }
                output.append(entry)
        return list(output)


class FacilityListView(FacilityTypeViewMixin, ListView):
    model = Facility
    template_name = "facility_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "loggedIn": self.request.user.is_authenticated,
            "grid": static("json/grid.geojson"),
            "name": context["facilitytype"].name,
            "url": reverse(
                "facilities:facility_list_geojson",
                kwargs={
                    "camp_slug": context["facilitytype"].responsible_team.camp.slug,
                    "facility_type_slug": context["facilitytype"].slug,
                },
            ),
        }
        return context

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(facility_type=self.facility_type)


class FacilityDetailView(FacilityTypeViewMixin, DetailView):
    model = Facility
    template_name = "facility_detail.html"
    pk_url_kwarg = "facility_uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "loggedIn": self.request.user.is_authenticated,
            "grid": static("json/grid.geojson"),
            "name": context["facility"].name,
            "description": context["facility"].description,
            "team": context["facility"].facility_type.responsible_team.name,
            "icon": context["facility"].facility_type.icon,
            "marker": context["facility"].facility_type.marker,
            "x": context["facility"].location.x,
            "y": context["facility"].location.y,
            "feedbackUrl": reverse(
                "facilities:facility_feedback",
                kwargs={
                    "camp_slug": context["facility"].camp.slug,
                    "facility_type_slug": context["facilitytype"].slug,
                    "facility_uuid": context["facility"].uuid,
                },
            ),
        }
        return context

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.prefetch_related("opening_hours")


class FacilityFeedbackView(FacilityTypeViewMixin, FacilityViewMixin, CreateView):
    model = FacilityFeedback
    template_name = "facility_feedback.html"
    fields = ["quick_feedback", "comment", "urgent"]

    def get_form(self, form_class=None):
        """- Add quick feedback field to the form
        - Add anon option to the form
        """
        form = super().get_form(form_class)

        form.fields["quick_feedback"] = forms.ModelChoiceField(
            queryset=self.facility_type.quickfeedback_options.all(),
            widget=forms.RadioSelect,
            empty_label=None,
            help_text=form.fields["quick_feedback"].help_text,
        )

        if self.request.user.is_authenticated:
            form.fields["anonymous"] = forms.BooleanField(
                label="Anonymous",
                required=False,
                help_text="Check if you prefer to submit this feedback without associating it with your bornhack.dk username",
            )
        return form

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["unhandled_feedbacks"] = FacilityFeedback.objects.filter(
            facility=self.facility,
            handled=False,
        ).count()
        return context

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.facility = self.facility
        if self.request.user.is_authenticated and not form.cleaned_data["anonymous"]:
            feedback.user = self.request.user
        feedback.save()
        messages.success(self.request, "Your feedback has been submitted. Thank you!")
        return redirect(
            reverse(
                "facilities:facility_feedback",
                kwargs={
                    "camp_slug": self.camp.slug,
                    "facility_type_slug": self.facility_type.slug,
                    "facility_uuid": self.facility.uuid,
                },
            ),
        )
