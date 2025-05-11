from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.detail import SingleObjectMixin

from camps.mixins import CampViewMixin
from program.utils import add_existing_availability_to_matrix
from program.utils import get_speaker_availability_form_matrix

from . import models


class EnsureCFPOpenMixin:
    def dispatch(self, request, *args, **kwargs):
        # do not permit this action if call for participation is not open
        if not self.camp.call_for_participation_open:
            messages.error(request, "The Call for Participation is not open.")
            return redirect(
                reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug}),
            )

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class EnsureUnapprovedProposalMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # do not permit editing if the proposal is already approved
        if self.get_object().proposal_status == models.UserSubmittedModel.PROPOSAL_APPROVED:
            messages.error(
                request,
                "This proposal has already been approved. Please contact the organisers if you need to modify something.",
            )
            return redirect(
                reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug}),
            )

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class EnsureWritableCampMixin:
    def dispatch(self, request, *args, **kwargs):
        # do not permit view if camp is in readonly mode
        if self.camp.read_only:
            messages.error(request, "No thanks")
            return redirect(
                reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug}),
            )

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class EnsureUserOwnsProposalMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # make sure that this proposal belongs to the logged in user
        if self.get_object().user.username != request.user.username:
            messages.error(request, "No thanks")
            return redirect(
                reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug}),
            )

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class UrlViewMixin:
    """Mixin with code shared between all the Url views"""

    def dispatch(self, request, *args, **kwargs):
        """Check that we have a valid SpeakerProposal or EventProposal and that it belongs to the current user"""
        # get the proposal
        if "event_uuid" in self.kwargs:
            self.event_proposal = get_object_or_404(
                models.EventProposal,
                uuid=self.kwargs["event_uuid"],
                user=request.user,
            )
        elif "speaker_uuid" in self.kwargs:
            self.speaker_proposal = get_object_or_404(
                models.SpeakerProposal,
                uuid=self.kwargs["speaker_uuid"],
                user=request.user,
            )
        else:
            # fuckery afoot
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Include the proposal in the template context"""
        context = super().get_context_data(**kwargs)
        if hasattr(self, "event_proposal") and self.event_proposal:
            context["event_proposal"] = self.event_proposal
        else:
            context["speaker_proposal"] = self.speaker_proposal
        return context

    def get_success_url(self):
        """Return to the detail view of the proposal"""
        if hasattr(self, "event_proposal"):
            return self.event_proposal.get_absolute_url()
        return self.speaker_proposal.get_absolute_url()


class EventViewMixin(CampViewMixin):
    """A mixin to get the Event object based on event_uuid in url kwargs"""

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.event = get_object_or_404(
            models.Event,
            track__camp=self.camp,
            slug=self.kwargs["event_slug"],
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["event"] = self.event
        return context


class EventFeedbackViewMixin(EventViewMixin):
    """A mixin to get the EventFeedback object based on self.event and self.request.user"""

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.event_feedback = get_object_or_404(
            models.EventFeedback,
            event=self.event,
            user=self.request.user,
        )

    def get_object(self):
        return self.event_feedback


class AvailabilityMatrixViewMixin(CampViewMixin):
    """Mixin with shared code between all availability matrix views,
    meaning all views that show an availability matrix (form or not)
    for a SpeakerProposal or Speaker object. Used by SpeakerProposal
    submitters and in backoffice.
    """

    def setup(self, *args, **kwargs):
        """Get the availability matrix"""
        super().setup(*args, **kwargs)
        # do we have an Event or an EventProposal?
        if hasattr(self.get_object(), "events"):
            # we have an Event
            event_types = models.EventType.objects.filter(
                events__in=self.get_object().events.all(),
            ).distinct()
        else:
            # we have an EventProposal
            event_types = models.EventType.objects.filter(
                event_proposals__in=self.get_object().event_proposals.all(),
            ).distinct()
        # get the matrix and add any existing availability to it
        self.matrix = get_speaker_availability_form_matrix(
            sessions=self.camp.event_sessions.filter(event_type__in=event_types),
        )
        add_existing_availability_to_matrix(self.matrix, self.get_object())

    def get_form_kwargs(self):
        """Add the matrix to form kwargs, only used if the view has a form"""
        kwargs = super().get_form_kwargs()
        kwargs["matrix"] = self.matrix
        return kwargs

    def get_initial(self, *args, **kwargs):
        """Populate the speaker_availability checkboxes, only used if the view has a form"""
        initial = super().get_initial(*args, **kwargs)

        # add initial checkbox states
        for date in self.matrix.keys():
            # loop over daychunks and check if we need a checkbox
            for daychunk in self.matrix[date].keys():
                if not self.matrix[date][daychunk]:
                    # we have no event_session here, carry on
                    continue
                if self.matrix[date][daychunk]["initial"] in [True, None]:
                    initial[self.matrix[date][daychunk]["fieldname"]] = True
                else:
                    initial[self.matrix[date][daychunk]["fieldname"]] = False

        # we are ready to render the form
        return initial

    def get_context_data(self, **kwargs):
        """Add the matrix to context"""
        context = super().get_context_data(**kwargs)
        context["matrix"] = self.matrix
        return context
