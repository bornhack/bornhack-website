import logging

from django.contrib import messages
from django.forms import modelformset_factory
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.edit import FormView

from camps.mixins import CampViewMixin
from program.models import Event
from program.models import EventFeedback
from program.models import Url
from program.models import UrlType

from ..forms import AddRecordingForm
from ..mixins import ContentTeamPermissionMixin

logger = logging.getLogger("bornhack.%s" % __name__)


class ApproveFeedbackView(CampViewMixin, ContentTeamPermissionMixin, FormView):
    """This view shows a list of EventFeedback objects which are pending approval."""

    model = EventFeedback
    template_name = "approve_feedback.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.queryset = EventFeedback.objects.filter(
            event__track__camp=self.camp,
            approved__isnull=True,
        )

        self.form_class = modelformset_factory(
            EventFeedback,
            fields=("approved",),
            min_num=self.queryset.count(),
            validate_min=True,
            max_num=self.queryset.count(),
            validate_max=True,
            extra=0,
        )

    def get_context_data(self, *args, **kwargs):
        """Include the queryset used for the modelformset_factory so we have
        some idea which object is which in the template
        Why the hell do the forms in the formset not include the object?
        """
        context = super().get_context_data(*args, **kwargs)
        context["event_feedback_list"] = self.queryset
        context["formset"] = self.form_class(queryset=self.queryset)
        return context

    def form_valid(self, form):
        form.save()
        if form.changed_objects:
            messages.success(
                self.request,
                f"Updated {len(form.changed_objects)} EventFeedbacks",
            )
        return redirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        return reverse(
            "backoffice:approve_event_feedback",
            kwargs={"camp_slug": self.camp.slug},
        )


class AddRecordingView(CampViewMixin, ContentTeamPermissionMixin, FormView):
    """This view shows a list of events that is set to be recorded, but without a recording URL attached."""

    model = Event
    template_name = "add_recording.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.queryset = Event.objects.filter(
            track__camp=self.camp,
            video_recording=True,
        ).exclude(urls__url_type__name="Recording")

        self.form_class = modelformset_factory(
            Event,
            form=AddRecordingForm,
            min_num=self.queryset.count(),
            validate_min=True,
            max_num=self.queryset.count(),
            validate_max=True,
            extra=0,
        )

    def get_context_data(self, *args, **kwargs):
        """Include the queryset used for the modelformset_factory so we have
        some idea which object is which in the template
        Why the hell do the forms in the formset not include the object?
        """
        context = super().get_context_data(*args, **kwargs)
        context["event_list"] = self.queryset
        context["formset"] = self.form_class(queryset=self.queryset)
        return context

    def form_valid(self, form):
        form.save()

        for event_data in form.cleaned_data:
            if event_data["recording_url"]:
                url = event_data["recording_url"]
                if not event_data["id"].urls.filter(url=url).exists():
                    recording_url = Url()
                    recording_url.event = event_data["id"]
                    recording_url.url = url
                    recording_url.url_type = UrlType.objects.get(name="Recording")
                    recording_url.save()

        if form.changed_objects:
            messages.success(self.request, f"Updated {len(form.changed_objects)} Event")
        return redirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        return reverse(
            "backoffice:add_eventrecording",
            kwargs={"camp_slug": self.camp.slug},
        )
