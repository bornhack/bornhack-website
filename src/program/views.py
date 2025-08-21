from __future__ import annotations

import logging
from collections import OrderedDict

import icalendar
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.template import Context
from django.template import Engine
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import View
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import UpdateView
from lxml import etree
from lxml import objectify

from camps.mixins import CampViewMixin
from utils.middleware import RedirectException
from utils.mixins import GetObjectMixin
from utils.mixins import UserIsObjectOwnerMixin
from utils.widgets import SliderWidget
from utils.widgets import SwitchWidget

from . import models
from .email import add_event_proposal_updated_email
from .email import add_new_event_proposal_email
from .email import add_new_speaker_proposal_email
from .email import add_speaker_proposal_updated_email
from .forms import EventProposalForm
from .forms import SpeakerProposalForm
from .mixins import AvailabilityMatrixViewMixin
from .mixins import EnsureCFPOpenMixin
from .mixins import EnsureUserOwnsProposalMixin
from .mixins import EnsureWritableCampMixin
from .mixins import EventFeedbackViewMixin
from .mixins import EventViewMixin
from .mixins import UrlViewMixin
from .multiform import MultiModelForm
from .utils import get_speaker_availability_form_matrix
from .utils import save_speaker_availability

logger = logging.getLogger(f"bornhack.{__name__}")


###################################################################
# ical calendar


class ICSView(CampViewMixin, View):
    def get(self, request, *args, **kwargs):
        query_kwargs = {}
        # Type query
        type_query = request.GET.get("type", None)
        if type_query:
            type_slugs = type_query.split(",")
            query_kwargs["event__event_type__in"] = models.EventType.objects.filter(
                slug__in=type_slugs,
            )

        # Location query
        location_query = request.GET.get("location", None)
        if location_query:
            location_slugs = location_query.split(",")
            query_kwargs["location__in"] = models.EventLocation.objects.filter(
                slug__in=location_slugs,
                camp=self.camp,
            )

        # Video recording query
        video_query = request.GET.get("video", None)
        if video_query:
            video_states = video_query.split(",")

            if "has-recording" in video_states:
                query_kwargs["event__video_url__isnull"] = False

            if "to-be-recorded" in video_states:
                query_kwargs["event__video_recording"] = True

            if "not-to-be-recorded" in video_states:
                query_kwargs.pop("event__video_recording", None)

        event_slots = models.EventSlot.objects.filter(
            event__track__camp=self.camp,
            **query_kwargs,
        ).prefetch_related("event", "event_session__event_location")

        cal = icalendar.Calendar()
        cal.add("prodid", "-//BornHack Website iCal Generator//bornhack.dk//")
        cal.add("version", "2.0")
        for slot in event_slots:
            cal.add_component(slot.get_ics_event())

        response = HttpResponse(cal.to_ical())
        response["Content-Type"] = "text/calendar"
        response["Content-Disposition"] = f"inline; filename={self.camp.slug}.ics"
        return response


###################################################################
# proposals list view


class ProposalListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = models.SpeakerProposal
    template_name = "proposal_list.html"
    context_object_name = "speaker_proposal_list"

    def get_queryset(self, **kwargs):
        """Only show speaker proposals for the current user."""
        return (
            super()
            .get_queryset()
            .filter(user=self.request.user)
            .prefetch_related(
                "event_proposals",
                "event_proposals__event_type",
                "urls__url_type",
                "speaker",
            )
        )

    def get_context_data(self, **kwargs):
        """Add event_proposals to the context."""
        context = super().get_context_data(**kwargs)
        context["event_proposal_list"] = models.EventProposal.objects.filter(
            track__camp=self.camp,
            user=self.request.user,
        ).prefetch_related("event_type", "track", "urls__url_type", "event", "speakers")
        context["event_type_list"] = models.EventType.objects.filter(public=True)
        return context


###################################################################
# speaker_proposal views


class SpeakerProposalCreateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    CreateView,
):
    """This view allows a user to create a new SpeakerProposal linked to an existing EventProposal."""

    model = models.SpeakerProposal
    template_name = "speaker_proposal_form.html"
    form_class = SpeakerProposalForm

    def setup(self, *args, **kwargs) -> None:
        """Get the event_proposal object and speaker availability matrix."""
        super().setup(*args, **kwargs)
        """ Get the event_proposal and availability matrix """
        self.event_proposal = get_object_or_404(
            models.EventProposal,
            pk=kwargs["event_uuid"],
        )
        self.matrix = get_speaker_availability_form_matrix(
            sessions=self.camp.event_sessions.filter(
                event_type=self.event_proposal.event_type,
            ),
        )

    def get_success_url(self):
        return reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})

    def get_form_kwargs(self):
        """Set camp and event_type for the form."""
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "camp": self.camp,
                "event_type": self.event_proposal.event_type,
                "matrix": self.matrix,
            },
        )
        return kwargs

    def get_initial(self, *args, **kwargs):
        """Populate the speaker_availability checkboxes."""
        initial = super().get_initial(*args, **kwargs)
        # loop over dates in the matrix
        for date in self.matrix:
            # loop over daychunks and check if we need a checkbox
            for daychunk in self.matrix[date]:
                if self.matrix[date][daychunk]:
                    # default to checked for new speakers
                    initial[self.matrix[date][daychunk]["fieldname"]] = True
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event_proposal"] = self.event_proposal
        context["matrix"] = self.matrix
        return context

    def form_valid(self, form):
        """Set user and camp before saving, then save availability."""
        speaker_proposal = form.save(commit=False)
        speaker_proposal.user = self.request.user
        speaker_proposal.camp = self.camp

        if not form.cleaned_data["email"]:
            # default to submitters email
            speaker_proposal.email = self.request.user.email

        # save speaker_proposal
        speaker_proposal = form.save()
        form.save_m2m()

        # then save speaker availability objects
        save_speaker_availability(form, speaker_proposal)

        # add speaker_proposal to event_proposal
        self.event_proposal.speakers.add(speaker_proposal)

        # send mail to content team
        if not add_new_speaker_proposal_email(speaker_proposal):
            logger.error(
                "Unable to send email to content team after new speaker_proposal",
            )

        return redirect(
            reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug}),
        )


class SpeakerProposalUpdateView(
    LoginRequiredMixin,
    AvailabilityMatrixViewMixin,
    EnsureWritableCampMixin,
    UserIsObjectOwnerMixin,
    EnsureCFPOpenMixin,
    UpdateView,
):
    """This view allows a user to update an existing SpeakerProposal."""

    model = models.SpeakerProposal
    template_name = "speaker_proposal_form.html"
    form_class = SpeakerProposalForm

    def get_object(self, queryset=None):
        """Prefetch availabilities for this SpeakerProposal."""
        qs = self.model.objects.filter(pk=self.kwargs.get(self.pk_url_kwarg))
        qs = qs.prefetch_related("availabilities")
        return qs.get()

    def get_form_kwargs(self):
        """Set camp, matrix and event_type for the form."""
        kwargs = super().get_form_kwargs()

        # get all event types this SpeakerProposal is involved in
        all_event_types = models.EventType.objects.filter(
            event_proposals__in=self.get_object().event_proposals.all(),
        ).distinct()

        if len(all_event_types) == 1:
            # use the event_type to customise the speaker form
            event_type = all_event_types[0]
        else:
            # more than one event_type for this speaker, show a non-generic form
            event_type = None

        # add camp and event_type to form kwargs
        kwargs.update(
            {"camp": self.camp, "event_type": event_type, "matrix": self.matrix},
        )
        return kwargs

    def form_valid(self, form):
        """Change status and save availability."""
        speaker_proposal = form.save(commit=False)

        # set proposal status to pending
        speaker_proposal.proposal_status = models.SpeakerProposal.PROPOSAL_PENDING

        if not speaker_proposal.email:
            # default to submitters email
            speaker_proposal.email = self.request.user.email

        # ok save() for real
        speaker_proposal.save()
        form.save_m2m()

        # then save speaker availability objects
        save_speaker_availability(form, speaker_proposal)

        # send mail to content team
        if not add_speaker_proposal_updated_email(speaker_proposal):
            logger.error(
                "Unable to send email to content team after speaker_proposal update",
            )

        # message user and redirect
        messages.info(
            self.request,
            "Changes to your proposal is now pending approval by the content team.",
        )
        return redirect(
            reverse(
                "program:speaker_proposal_detail",
                kwargs={"camp_slug": self.camp.slug, "pk": speaker_proposal.pk},
            ),
        )


class SpeakerProposalDeleteView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureUserOwnsProposalMixin,
    EnsureCFPOpenMixin,
    DeleteView,
):
    """This view allows a user to delete an existing SpeakerProposal object, as long as it is not linked to any EventProposals."""

    model = models.SpeakerProposal
    template_name = "proposal_delete.html"

    def get(self, request, *args, **kwargs):
        # do not permit deleting if this speaker_proposal is linked to any event_proposals
        if self.get_object().event_proposals.exists():
            messages.error(
                request,
                "Cannot delete a person while it is associated with one or more event_proposals. Delete those first.",
            )
            return redirect(
                reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug}),
            )

        # continue with the request
        return super().get(request, *args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delete availabilities before deleting the proposal."""
        self.get_object().availabilities.all().delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            f"Proposal '{self.object.name}' has been deleted.",
        )
        return reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})


class SpeakerProposalDetailView(
    LoginRequiredMixin,
    AvailabilityMatrixViewMixin,
    EnsureUserOwnsProposalMixin,
    DetailView,
):
    model = models.SpeakerProposal
    template_name = "speaker_proposal_detail.html"
    context_object_name = "speaker_proposal"


###################################################################
# event_proposal views


class EventProposalTypeSelectView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    ListView,
):
    """This view is for selecting the type of event to submit (when adding a new event_proposal to an existing speaker_proposal)."""

    model = models.EventType
    template_name = "event_type_select.html"
    context_object_name = "event_type_list"

    def setup(self, *args, **kwargs) -> None:
        """Get the speaker_proposal object."""
        super().setup(*args, **kwargs)
        self.speaker = get_object_or_404(
            models.SpeakerProposal,
            pk=kwargs["speaker_uuid"],
        )

    def get_queryset(self, **kwargs):
        """We only allow submissions of events with EventTypes where public=True."""
        return super().get_queryset().filter(public=True)

    def get_context_data(self, *args, **kwargs):
        """Make speaker_proposal object available in template."""
        context = super().get_context_data(**kwargs)
        context["speaker"] = self.speaker
        return context


class EventProposalSelectPersonView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    ListView,
):
    """This view is for selecting an existing speaker_proposal to add to an existing event_proposal."""

    model = models.SpeakerProposal
    template_name = "event_proposal_select_person.html"
    context_object_name = "speaker_proposal_list"

    def dispatch(self, request, *args, **kwargs):
        """Get EventProposal from url kwargs."""
        self.event_proposal = get_object_or_404(
            models.EventProposal,
            pk=kwargs["event_uuid"],
            user=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        """Filter out any speaker_proposals already added to this event_proposal."""
        return self.event_proposal.get_available_speaker_proposals().all()

    def get_context_data(self, *args, **kwargs):
        """Make event_proposal object available in template."""
        context = super().get_context_data(**kwargs)
        context["event_proposal"] = self.event_proposal
        return context


class EventProposalAddPersonView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UpdateView,
):
    """This view is for adding an existing speaker_proposal to an existing event_proposal."""

    model = models.EventProposal
    template_name = "event_proposal_add_person.html"
    fields = []
    pk_url_kwarg = "event_uuid"
    context_object_name = "event_proposal"

    def dispatch(self, request, *args, **kwargs):
        """Get the speaker_proposal object."""
        self.speaker_proposal = get_object_or_404(
            models.SpeakerProposal,
            pk=kwargs["speaker_uuid"],
            user=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Make speaker_proposal object available in template."""
        context = super().get_context_data(**kwargs)
        context["speaker_proposal"] = self.speaker_proposal
        return context

    def form_valid(self, form):
        form.instance.speakers.add(self.speaker_proposal)
        messages.success(
            self.request,
            f"{self.speaker_proposal.name} has been added as {form.instance.event_type.host_title} for {form.instance.title}",
        )
        return redirect(self.get_success_url())


class EventProposalRemovePersonView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UpdateView,
):
    """This view is for removing a speaker_proposal from an existing event_proposal."""

    model = models.EventProposal
    template_name = "event_proposal_remove_person.html"
    fields = []
    pk_url_kwarg = "event_uuid"

    def dispatch(self, request, *args, **kwargs):
        """Get the speaker_proposal object and check a few things."""
        # get the speaker_proposal object from URL kwargs
        self.speaker_proposal = get_object_or_404(
            models.SpeakerProposal,
            pk=kwargs["speaker_uuid"],
            user=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Make speaker_proposal object available in template."""
        context = super().get_context_data(**kwargs)
        context["speaker_proposal"] = self.speaker_proposal
        return context

    def form_valid(self, form):
        """Remove the speaker from the event."""
        if self.speaker_proposal not in self.get_object().speakers.all():
            # this speaker is not associated with this event
            raise Http404

        if self.get_object().speakers.count() == 1:
            messages.error(
                self.request,
                "Cannot delete the last person associalted with event!",
            )
            return redirect(self.get_success_url())

        # remove speaker_proposal from event_proposal
        form.instance.speakers.remove(self.speaker_proposal)
        messages.success(
            self.request,
            f"{self.speaker_proposal.name} has been removed from {self.get_object().title}",
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "program:event_proposal_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.get_object().uuid},
        )


class EventProposalCreateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    CreateView,
):
    """This view allows a user to create a new event_proposal linked to an existing speaker_proposal."""

    model = models.EventProposal
    template_name = "event_proposal_form.html"
    form_class = EventProposalForm

    def setup(self, *args, **kwargs) -> None:
        """Get the speaker_proposal object."""
        super().setup(*args, **kwargs)
        self.speaker_proposal = get_object_or_404(
            models.SpeakerProposal,
            pk=self.kwargs["speaker_uuid"],
        )
        self.event_type = get_object_or_404(
            models.EventType,
            slug=self.kwargs["event_type_slug"],
        )

    def get_context_data(self, *args, **kwargs):
        """Make speaker_proposal object available in template."""
        context = super().get_context_data(**kwargs)
        context["speaker"] = self.speaker_proposal
        context["event_type"] = self.event_type
        return context

    def get_form_kwargs(self):
        """Set camp and event_type for the form."""
        kwargs = super().get_form_kwargs()
        kwargs.update({"camp": self.camp, "event_type": self.event_type})
        return kwargs

    def form_valid(self, form):
        """Set camp and user for this event_proposal, save slideurl."""
        event_proposal = form.save(commit=False)
        event_proposal.user = self.request.user
        event_proposal.event_type = self.event_type

        # save for real
        event_proposal.save()
        form.save_m2m()

        # save or update slides url
        slideurl = form.cleaned_data.get("slides_url")
        if slideurl:
            slides_url, created = models.Url.objects.get_or_create(
                event_proposal=event_proposal,
                url_type=models.UrlType.objects.get(name="Slides"),
                defaults={"url": slideurl},
            )

        # add the speaker_proposal to the event_proposal
        event_proposal.speakers.add(self.speaker_proposal)

        # send mail to content team
        if not add_new_event_proposal_email(event_proposal):
            logger.error(
                "Unable to send email to content team after new event_proposal",
            )

        messages.success(
            self.request,
            "Your event proposal is now pending approval by the content team.",
        )

        # all good
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})


class EventProposalUpdateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureUserOwnsProposalMixin,
    EnsureCFPOpenMixin,
    UpdateView,
):
    model = models.EventProposal
    template_name = "event_proposal_form.html"
    form_class = EventProposalForm

    def get_form_kwargs(self):
        """Set camp and event_type for the form."""
        kwargs = super().get_form_kwargs()
        kwargs.update({"camp": self.camp, "event_type": self.get_object().event_type})
        return kwargs

    def get_context_data(self, *args, **kwargs):
        """Make speaker_proposal and event_type objects available in the template."""
        context = super().get_context_data(**kwargs)
        context["event_type"] = self.get_object().event_type
        return context

    def form_valid(self, form):
        # set status to pending and save event_proposal
        event_proposal = form.save(commit=False)
        event_proposal.proposal_status = models.EventProposal.PROPOSAL_PENDING

        # save or update slides url
        slideurl = form.cleaned_data.get("slides_url")
        if slideurl:
            slides_url, created = models.Url.objects.get_or_create(
                event_proposal=event_proposal,
                url_type=models.UrlType.objects.get(name="Slides"),
                defaults={"url": slideurl},
            )

        # save for real
        event_proposal.save()
        form.save_m2m()

        # send email to content team
        if not add_event_proposal_updated_email(event_proposal):
            logger.error(
                "Unable to send email to content team after event_proposal update",
            )

        # message for the user and redirect
        messages.info(
            self.request,
            "Changes to your event proposal is now pending approval by the content team.",
        )
        return redirect(
            reverse(
                "program:event_proposal_detail",
                kwargs={"camp_slug": self.camp.slug, "pk": event_proposal.pk},
            ),
        )


class EventProposalDeleteView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureUserOwnsProposalMixin,
    EnsureCFPOpenMixin,
    DeleteView,
):
    model = models.EventProposal
    template_name = "proposal_delete.html"

    def get_success_url(self):
        messages.success(
            self.request,
            f"Proposal '{self.object.title}' has been deleted.",
        )
        return reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})


class EventProposalDetailView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureUserOwnsProposalMixin,
    DetailView,
):
    model = models.EventProposal
    template_name = "event_proposal_detail.html"
    context_object_name = "event_proposal"


###################################################################
# combined proposal views


class CombinedProposalTypeSelectView(LoginRequiredMixin, CampViewMixin, ListView):
    """A view which allows the user to select event type without anything else on the page."""

    model = models.EventType
    template_name = "event_type_select.html"

    def get_queryset(self, **kwargs):
        """We only allow submissions of events with EventTypes where public=True."""
        return super().get_queryset().filter(public=True)


class CombinedProposalPersonSelectView(LoginRequiredMixin, CampViewMixin, ListView):
    """A view which allows the user to 1) choose between existing SpeakerProposals or
    2) pressing a button to create a new SpeakerProposal.
    Redirect straight to 2) if no existing SpeakerProposals exist.
    """

    model = models.SpeakerProposal
    template_name = "combined_proposal_select_person.html"
    context_object_name = "speaker_proposal_list"

    def setup(self, *args, **kwargs) -> None:
        """Check that we have a valid EventType."""
        super().setup(*args, **kwargs)
        self.event_type = get_object_or_404(
            models.EventType,
            slug=self.kwargs["event_type_slug"],
        )

    def get_queryset(self, **kwargs):
        """Only show speaker proposals for the current user."""
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """Add EventType to template context."""
        context = super().get_context_data(**kwargs)
        context["event_type"] = self.event_type
        return context

    def get(self, request, *args, **kwargs):
        """If we don't have any existing SpeakerProposals just redirect directly to the combined submit view."""
        if not self.get_queryset().exists():
            return redirect(
                reverse_lazy(
                    "program:proposal_combined_submit",
                    kwargs={
                        "camp_slug": self.camp.slug,
                        "event_type_slug": self.event_type.slug,
                    },
                ),
            )
        return super().get(request, *args, **kwargs)


class CombinedProposalSubmitView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureCFPOpenMixin,
    CreateView,
):
    """This view is used by users to submit CFP proposals.
    It allows the user to submit an EventProposal and a SpeakerProposal together.
    """

    template_name = "combined_proposal_submit.html"

    def setup(self, *args, **kwargs) -> None:
        """Check that we have a valid EventType in url kwargs."""
        super().setup(*args, **kwargs)
        self.event_type = get_object_or_404(
            models.EventType,
            slug=self.kwargs["event_type_slug"],
        )

        self.matrix = get_speaker_availability_form_matrix(
            sessions=self.camp.event_sessions.filter(
                event_type=self.event_type,
            ).prefetch_related("event_type"),
        )

    def get_context_data(self, **kwargs):
        """Add EventType to template context."""
        context = super().get_context_data(**kwargs)
        context["event_type"] = self.event_type
        context["matrix"] = self.matrix
        return context

    def form_valid(self, form):
        """Save the object(s) here before redirecting."""
        # first save the SpeakerProposal
        speaker_proposal = form["speaker_proposal"].save(commit=False)
        speaker_proposal.camp = self.camp
        speaker_proposal.user = self.request.user
        if not speaker_proposal.email:
            speaker_proposal.email = self.request.user.email
        speaker_proposal.save()
        form["speaker_proposal"].save_m2m()

        # then save speaker availability objects
        save_speaker_availability(form["speaker_proposal"], speaker_proposal)

        # then save the event_proposal
        event_proposal = form["event_proposal"].save(commit=False)
        event_proposal.user = self.request.user
        event_proposal.event_type = self.event_type
        event_proposal.save()
        form["event_proposal"].save_m2m()

        # save or update slides url
        slideurl = form.cleaned_data.get("slides_url")
        if slideurl:
            slides_url, created = models.Url.objects.get_or_create(
                event_proposal=event_proposal,
                url_type=models.UrlType.objects.get(name="Slides"),
                defaults={"url": slideurl},
            )

        # add the speaker_proposal to the event_proposal
        event_proposal.speakers.add(speaker_proposal)

        # send mail(s) to content team
        if not add_new_event_proposal_email(event_proposal):
            logger.error(
                "Unable to send email to content team after new event_proposal",
            )
        if not hasattr(self, "speaker_proposal") and not add_new_speaker_proposal_email(speaker_proposal):
            logger.error(
                "Unable to send email to content team after new speaker_proposal",
            )

        messages.success(
            self.request,
            f"Your {self.event_type.host_title} proposal and {self.event_type.name} proposal have been submitted for review. You will receive an email when they have been accepted or rejected.",
        )

        # all good
        return redirect(
            reverse_lazy("program:proposal_list", kwargs={"camp_slug": self.camp.slug}),
        )

    def get_form_class(self):
        """We must show two forms on the page.
        We use betterforms.MultiModelForm to combine two forms.
        """

        # build our MultiModelForm
        class CombinedProposalSubmitForm(MultiModelForm):
            form_classes = OrderedDict(
                (
                    ("speaker_proposal", SpeakerProposalForm),
                    ("event_proposal", EventProposalForm),
                ),
            )

        # return the form class
        return CombinedProposalSubmitForm

    def get_form_kwargs(self):
        """Set camp and event_type and matrix for the form."""
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {"camp": self.camp, "event_type": self.event_type, "matrix": self.matrix},
        )
        return kwargs

    def get_initial(self):
        """We default to True for all daychunks in the speaker availability table
        when submitting a new speaker.
        """
        initial = super().get_initial()
        # we use betterforms.MultiModelForm so our initial dict has to be nested,
        # make sure we have a speaker_proposal dict to work with
        if "speaker_proposal" not in initial:
            initial["speaker_proposal"] = {}
        # loop over days in the matrix
        for date in self.matrix:
            # loop over the daychunks on this day
            for daychunk in self.matrix[date]:
                # do we have/want a checkbox here?
                if self.matrix[date][daychunk]:
                    # all initial values for news speakers should be True/checked
                    initial["speaker_proposal"][self.matrix[date][daychunk]["fieldname"]] = True
                    # but we set the initial in the dict to None to indicate we have no info
                    self.matrix[date][daychunk]["initial"] = None
        return initial


###################################################################
# speaker views


class SpeakerDetailView(CampViewMixin, DetailView):
    model = models.Speaker
    template_name = "speaker_detail.html"


class SpeakerListView(CampViewMixin, ListView):
    model = models.Speaker
    template_name = "speaker_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.prefetch_related("events__event_type")


###################################################################
# event views


class EventListView(CampViewMixin, ListView):
    model = models.Event
    template_name = "event_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.prefetch_related(
            "event_type",
            "track",
            "speakers",
            "event_slots__event_session__event_location",
            "tags",
        )


class EventDetailView(CampViewMixin, DetailView):
    model = models.Event
    template_name = "event_detail.html"
    slug_url_kwarg = "event_slug"


###################################################################
# schedule views


class ScheduleView(CampViewMixin, TemplateView):
    template_name = "schedule_view.html"

    def setup(self, *args, **kwargs) -> None:
        """If no events are scheduled redirect to the event page."""
        super().setup(*args, **kwargs)

        # we redirect to the list of events if we dont show the schedule
        event_list_url = reverse(
            "program:event_index",
            kwargs={"camp_slug": self.camp.slug},
        )

        # do we have a schedule to show?
        if not self.camp.event_slots.filter(event__isnull=False).exists():
            raise RedirectException(event_list_url)

        # if camp.show_schedule is False we only show it to superusers
        if not self.camp.show_schedule and not self.request.user.is_superuser:
            raise RedirectException(event_list_url)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event_slots"] = (
            models.EventSlot.objects.filter(event__track__camp=self.camp)
            .prefetch_related(
                "event_session__event_location",
                "event_session__event_type",
                "event__speakers",
                "event__tags",
                "event__event_type",
            )
            .order_by("when")
        )
        return context


class CallForParticipationView(CampViewMixin, TemplateView):
    template_name = "call_for_participation.html"


class FrabXmlView(CampViewMixin, View):
    """This view returns an XML schedule in Frab format
    XSD is from https://raw.githubusercontent.com/wiki/frab/frab/images/schedule.xsd.
    """

    def get(self, *args, **kwargs):
        # get all EventSlots with something scheduled
        qs = (
            models.EventSlot.objects.filter(event__track__camp=self.camp)
            .prefetch_related(
                "event__urls",
                "event__speakers",
                "event_session__event_location",
            )
            .order_by("when", "event_session__event_location")
        )
        E = objectify.ElementMaker(annotate=False)
        days = ()
        i = 0
        # loop over days
        for day in self.camp.get_days("camp")[:-1]:
            i += 1
            # build a tuple of locations
            locations = ()
            # loop over locations
            for location in models.EventLocation.objects.filter(
                id__in=qs.filter(event__isnull=False).values_list(
                    "event_session__event_location_id",
                    flat=True,
                ),
            ):
                # build a tuple of scheduled events at this location
                instances = ()
                for slot in qs.filter(
                    when__contained_by=day,
                    event_session__event_location=location,
                ):
                    # build a tuple of speakers for this event
                    speakers = ()
                    for speaker in slot.event.speakers.all():
                        speakers += (E.person(speaker.name, id=str(speaker.pk)),)

                    # build a tuple of URLs for this Event
                    urls = ()
                    for url in slot.event.urls.all():
                        urls += (E.link(url.url_type.name, href=url.url),)

                    # add this event to the instances tuple
                    instances += (
                        E.event(
                            E.date(slot.when.lower.isoformat()),
                            E.start(slot.when.lower.time()),
                            E.duration(slot.event.duration),
                            E.room(location.name),
                            E.slug(f"{slot.pk}-{slot.event.slug}"),
                            E.url(
                                self.request.build_absolute_uri(
                                    slot.event.get_absolute_url(),
                                ),
                            ),
                            E.recording(
                                E.license("CC BY-SA 4.0"),
                                E.optout(
                                    "false" if slot.event.video_recording else "true",
                                ),
                            ),
                            E.title(slot.event.title),
                            # our Events have no subtitle
                            E.subtitle(""),
                            E.track(slot.event.track),
                            E.type(slot.event.event_type),
                            # our Events have no language attribute but are mostly english
                            E.language("en"),
                            E.abstract(slot.event.abstract),
                            # our Events have no long description
                            E.description(""),
                            E.persons(*speakers),
                            E.links(*urls),
                            E.attachments,
                            id=str(slot.id),
                            guid=str(slot.uuid),
                        ),
                    )
                # add the events for this location on this day to the locations tuple
                locations += (E.room(*instances, name=location.name),)

            # add this day to the days tuple
            days += (
                E.day(
                    *locations,
                    index=str(i),
                    date=str(day.lower.date()),
                    start=day.lower.isoformat(),
                    end=day.upper.isoformat(),
                ),
            )

        # put the XML together
        xml = E.schedule(
            E.version("BornHack Frab XML Generator v2.0"),
            E.conference(
                E.title(self.camp.title),
                E.acronym(str(self.camp.camp.lower.year)),
                E.start(self.camp.camp.lower.date().isoformat()),
                E.end(self.camp.camp.upper.date().isoformat()),
                E.days(len(self.camp.get_days("camp"))),
                E.timeslot_duration("00:30"),
                E.base_url(self.request.build_absolute_uri("/")),
            ),
            *days,
        )
        xml = etree.tostring(xml, pretty_print=True, xml_declaration=True)

        # let's play nice - validate the XML before returning it
        schema = etree.XMLSchema(file="program/xsd/schedule.xml.xsd")
        parser = objectify.makeparser(schema=schema)
        try:
            objectify.fromstring(xml, parser)
        except etree.XMLSyntaxError:
            # we are generating invalid XML
            logger.exception("Something went sideways when validating frab xml :(")
            return HttpResponseServerError()
        response = HttpResponse(content_type="application/xml")
        response.write(xml)
        return response


###################################################################
# control center csv


class ProgramControlCenter(CampViewMixin, TemplateView):
    template_name = "control/index.html"

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        proposals = models.EventProposal.objects.filter(camp=self.camp).select_related(
            "user",
            "event",
        )
        context["proposals"] = proposals

        engine = Engine.get_default()
        template = engine.get_template("control/proposal_overview.csv")
        csv = template.render(Context(context))
        context["csv"] = csv

        return context


###################################################################
# URL views


class UrlCreateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UrlViewMixin,
    CreateView,
):
    model = models.Url
    template_name = "url_form.html"
    fields = ["url_type", "url"]

    def form_valid(self, form):
        """Set the proposal FK before saving
        Set proposal as pending if it isn't already.
        """
        if hasattr(self, "event_proposal") and self.event_proposal:
            # this URL belongs to an event_proposal
            form.instance.event_proposal = self.event_proposal
            form.save()
            if self.event_proposal.proposal_status != models.SpeakerProposal.PROPOSAL_PENDING:
                self.event_proposal.proposal_status = models.SpeakerProposal.PROPOSAL_PENDING
                self.event_proposal.save()
                messages.success(
                    self.request,
                    f"{self.event_proposal.title} is now pending review by the Content Team.",
                )
        else:
            # this URL belongs to a speaker_proposal
            form.instance.speaker_proposal = self.speaker_proposal
            form.save()
            if self.speaker_proposal.proposal_status != models.SpeakerProposal.PROPOSAL_PENDING:
                self.speaker_proposal.proposal_status = models.SpeakerProposal.PROPOSAL_PENDING
                self.speaker_proposal.save()
                messages.success(
                    self.request,
                    f"{self.speaker_proposal.name} is now pending review by the Content Team.",
                )

        messages.success(self.request, "URL saved.")

        # all good
        return redirect(
            reverse_lazy("program:proposal_list", kwargs={"camp_slug": self.camp.slug}),
        )


class UrlUpdateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UrlViewMixin,
    UpdateView,
):
    model = models.Url
    template_name = "url_form.html"
    fields = ["url_type", "url"]
    pk_url_kwarg = "url_uuid"

    def form_valid(self, form):
        """Set proposal as pending if it isn't already."""
        if hasattr(self, "event_proposal") and self.event_proposal:
            # this URL belongs to an event_proposal
            form.save()
            if self.event_proposal.proposal_status != models.SpeakerProposal.PROPOSAL_PENDING:
                self.event_proposal.proposal_status = models.SpeakerProposal.PROPOSAL_PENDING
                self.event_proposal.save()
                messages.success(
                    self.request,
                    f"{self.event_proposal.title} is now pending review by the Content Team.",
                )
        else:
            # this URL belongs to a speaker_proposal
            form.save()
            if self.speaker_proposal.proposal_status != models.SpeakerProposal.PROPOSAL_PENDING:
                self.speaker_proposal.proposal_status = models.SpeakerProposal.PROPOSAL_PENDING
                self.speaker_proposal.save()
                messages.success(
                    self.request,
                    f"{self.speaker_proposal.name} is now pending review by the Content Team.",
                )

        messages.success(self.request, "URL saved.")

        # all good
        return redirect(
            reverse_lazy("program:proposal_list", kwargs={"camp_slug": self.camp.slug}),
        )


class UrlDeleteView(
    GetObjectMixin,
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UrlViewMixin,
    DeleteView,
):
    model = models.Url
    template_name = "url_delete.html"
    pk_url_kwarg = "url_uuid"

    def delete(self, request, *args, **kwargs):
        """Set proposal as pending if it isn't already."""
        if hasattr(self, "event_proposal") and self.event_proposal:
            # this URL belongs to a speaker_proposal
            if self.event_proposal.proposal_status != models.SpeakerProposal.PROPOSAL_PENDING:
                self.event_proposal.proposal_status = models.SpeakerProposal.PROPOSAL_PENDING
                self.event_proposal.save()
                messages.success(
                    self.request,
                    f"{self.event_proposal.title} is now pending review by the Content Team.",
                )
        # this URL belongs to a speaker_proposal
        elif self.speaker_proposal.proposal_status != models.SpeakerProposal.PROPOSAL_PENDING:
            self.speaker_proposal.proposal_status = models.SpeakerProposal.PROPOSAL_PENDING
            self.speaker_proposal.save()
            messages.success(
                self.request,
                f"{self.speaker_proposal.name} is now pending review by the Content Team.",
            )

        self.object.delete()
        messages.success(self.request, "URL deleted.")

        # all good
        return redirect(
            reverse_lazy("program:proposal_list", kwargs={"camp_slug": self.camp.slug}),
        )


###################################################################
# Feedback views


class FeedbackRedirectView(LoginRequiredMixin, EventViewMixin, DetailView):
    """Redirect to the appropriate view."""

    model = models.Event
    slug_url_kwarg = "event_slug"

    def setup(self, *args, **kwargs) -> None:
        super().setup(*args, **kwargs)
        if not self.request.user.is_authenticated:
            messages.error(
                self.request,
                "You must be logged in to provide Event Feedback",
            )
            raise RedirectException(
                reverse(
                    "program:event_detail",
                    kwargs={
                        "camp_slug": self.camp.slug,
                        "event_slug": self.event.slug,
                    },
                ),
            )

        if self.event.proposal.user == self.request.user:
            # user is owner of the event
            raise RedirectException(
                reverse(
                    "program:event_feedback_list",
                    kwargs={
                        "camp_slug": self.camp.slug,
                        "event_slug": self.event.slug,
                    },
                ),
            )

        if self.event.feedbacks.filter(user=self.request.user).exists():
            # user has existing feedback
            raise RedirectException(
                reverse(
                    "program:event_feedback_detail",
                    kwargs={"camp_slug": self.camp.slug, "event_slug": self.event.slug},
                ),
            )

        # user has no existing feedback
        raise RedirectException(
            reverse(
                "program:event_feedback_create",
                kwargs={"camp_slug": self.camp.slug, "event_slug": self.event.slug},
            ),
        )


class FeedbackListView(LoginRequiredMixin, EventViewMixin, ListView):
    """The FeedbackListView is used by the event owner to see approved Feedback for the Event."""

    model = models.EventFeedback
    template_name = "event_feedback_list.html"
    context_object_name = "event_feedback_list"

    def setup(self, *args, **kwargs) -> None:
        super().setup(*args, **kwargs)
        if not self.event.proposal or self.event.proposal.user != self.request.user:
            messages.error(self.request, "Only the event owner can read feedback!")
            raise RedirectException(
                reverse(
                    "program:event_detail",
                    kwargs={"camp_slug": self.camp.slug, "event_slug": self.event.slug},
                ),
            )

    def get_queryset(self, *args, **kwargs):
        return models.EventFeedback.objects.filter(event=self.event, approved=True)


class FeedbackCreateView(LoginRequiredMixin, EventViewMixin, CreateView):
    """Used by users to create Feedback for an Event. Available to all logged in users."""

    model = models.EventFeedback
    fields = ["expectations_fulfilled", "attend_speaker_again", "rating", "comment"]
    template_name = "event_feedback_form.html"

    def setup(self, *args, **kwargs) -> None:
        super().setup(*args, **kwargs)
        if not self.request.user.is_authenticated:
            messages.error(
                self.request,
                "You must be logged in to provide Event Feedback",
            )
            raise RedirectException(
                reverse(
                    "program:event_detail",
                    kwargs={
                        "camp_slug": self.camp.slug,
                        "event_slug": self.event.slug,
                    },
                ),
            )

        if models.EventFeedback.objects.filter(
            event=self.event,
            user=self.request.user,
        ).exists():
            raise RedirectException(
                reverse(
                    "program:event_feedback_detail",
                    kwargs={"camp_slug": self.camp.slug, "event_slug": self.event.slug},
                ),
            )

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["expectations_fulfilled"].widget = SwitchWidget()
        form.fields["attend_speaker_again"].widget = SwitchWidget()
        form.fields["rating"].widget = SliderWidget(
            attrs={"min": 1, "max": 5},
        )
        return form

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.user = self.request.user
        feedback.event = self.event
        feedback.save()
        messages.success(
            self.request,
            "Your feedback was submitted, it is now pending approval.",
        )
        return redirect(feedback.get_absolute_url())


class FeedbackDetailView(
    LoginRequiredMixin,
    EventFeedbackViewMixin,
    UserIsObjectOwnerMixin,
    DetailView,
):
    """Used by the EventFeedback owner to see their own feedback."""

    model = models.EventFeedback
    template_name = "event_feedback_detail.html"
    context_object_name = "event_feedback"


class FeedbackUpdateView(
    LoginRequiredMixin,
    EventFeedbackViewMixin,
    UserIsObjectOwnerMixin,
    UpdateView,
):
    """Used by the EventFeedback owner to update their feedback."""

    model = models.EventFeedback
    fields = ["expectations_fulfilled", "attend_speaker_again", "rating", "comment"]
    template_name = "event_feedback_form.html"

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.approved = False
        feedback.save()
        messages.success(self.request, "Your feedback was updated")
        return redirect(feedback.get_absolute_url())


class FeedbackDeleteView(
    LoginRequiredMixin,
    EventFeedbackViewMixin,
    UserIsObjectOwnerMixin,
    DeleteView,
):
    """Used by the EventFeedback owner to delete their own feedback."""

    model = models.EventFeedback
    template_name = "event_feedback_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Your feedback was deleted")
        return self.event.get_absolute_url()
