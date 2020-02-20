from camps.mixins import CampViewMixin
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView

from .mixins import FacilityTypeViewMixin, FacilityViewMixin
from .models import Facility, FacilityFeedback, FacilityType


class FacilityTypeListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = FacilityType
    template_name = "facility_type_list.html"


class FacilityListView(LoginRequiredMixin, FacilityTypeViewMixin, ListView):
    model = Facility
    template_name = "facility_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(facility_type=self.facility_type)


class FacilityDetailView(LoginRequiredMixin, FacilityTypeViewMixin, DetailView):
    model = Facility
    template_name = "facility_detail.html"
    pk_url_kwarg = "facility_uuid"


class FacilityFeedbackView(FacilityViewMixin, CreateView):
    model = FacilityFeedback
    template_name = "facility_feedback.html"
    fields = ["quick_feedback", "comment", "urgent"]

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        return initial

    def get_form(self, form_class=None):
        """
        - Add anon option to the form
        """
        form = super().get_form(form_class)

        form.fields["quick_feedback"] = forms.ModelChoiceField(
            queryset=self.facility_type.quickfeedback_options.all(),
            widget=forms.RadioSelect,
            empty_label=None,
            help_text=form.fields["quick_feedback"].help_text,
        )

        form.fields["anonymous"] = forms.BooleanField(
            label="Anonymous",
            required=False,
            help_text="Check if you prefer to submit this feedback without associating it with your bornhack.dk username",
        )
        return form

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["unhandled_feedbacks"] = FacilityFeedback.objects.filter(
            facility=self.facility, handled=False
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
            )
        )
