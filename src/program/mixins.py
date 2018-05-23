from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from . import models
from django.contrib import messages
from django.http import Http404, HttpResponse


class EnsureCFPOpenMixin(object):
    def dispatch(self, request, *args, **kwargs):
        # do not permit this action if call for participation is not open
        if not self.camp.call_for_participation_open:
            messages.error(request, "The Call for Participation is not open.")
            return redirect(
                reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug})
            )

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class EnsureUnapprovedProposalMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # do not permit editing if the proposal is already approved
        if self.get_object().proposal_status == models.UserSubmittedModel.PROPOSAL_APPROVED:
            messages.error(request, "This proposal has already been approved. Please contact the organisers if you need to modify something.")
            return redirect(reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug}))

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class EnsureWritableCampMixin(object):
    def dispatch(self, request, *args, **kwargs):
        # do not permit view if camp is in readonly mode
        if self.camp.read_only:
            messages.error(request, "No thanks")
            return redirect(reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug}))

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class EnsureUserOwnsProposalMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # make sure that this proposal belongs to the logged in user
        if self.get_object().user.username != request.user.username:
            messages.error(request, "No thanks")
            return redirect(
                reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug})
            )

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class UrlViewMixin(object):
    """
    Mixin with code shared between all the Url views
    """
    def dispatch(self, request, *args, **kwargs):
        """
        Check that we have a valid SpeakerProposal or EventProposal and that it belongs to the current user
        """
        # get the proposal
        if 'event_uuid' in self.kwargs:
            self.eventproposal = get_object_or_404(models.EventProposal, uuid=self.kwargs['event_uuid'], user=request.user)
        elif 'speaker_uuid' in self.kwargs:
            self.speakerproposal = get_object_or_404(models.SpeakerProposal, uuid=self.kwargs['speaker_uuid'], user=request.user)
        else:
            # fuckery afoot
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Include the proposal in the template context
        """
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'eventproposal') and self.eventproposal:
            context['eventproposal'] = self.eventproposal
        else:
            context['speakerproposal'] = self.speakerproposal
        return context

    def get_success_url(self):
        """
        Return to the detail view of the proposal
        """
        if hasattr(self, 'eventproposal'):
            return self.eventproposal.get_absolute_url()
        else:
            return self.speakerproposal.get_absolute_url()

