from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import redirect
from django.urls import reverse
from . import models
from django.contrib import messages
from django.http import Http404, HttpResponse
import sys
import mimetypes


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

