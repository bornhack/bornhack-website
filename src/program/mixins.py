import os
import logging
from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from . import models
from django.contrib import messages
from django.http import Http404

from sendfile import sendfile

logger = logging.getLogger("bornhack.%s" % __name__)


class EnsureCFSOpenMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # do not permit editing if call for speakers is not open
        if not self.camp.call_for_speakers_open:
            messages.error(request, "The Call for Speakers is not open.")
            return redirect(reverse('proposal_list', kwargs={'camp_slug': self.camp.slug}))

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class CreateProposalMixin(SingleObjectMixin):
    def form_valid(self, form):
        # set camp and user before saving
        form.instance.camp = self.camp
        form.instance.user = self.request.user
        speaker = form.save()
        return redirect(reverse('proposal_list', kwargs={'camp_slug': self.camp.slug}))


class EnsureUnapprovedProposalMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # do not permit editing if the proposal is already approved
        if self.get_object().proposal_status == models.UserSubmittedModel.PROPOSAL_APPROVED:
            messages.error(request, "This proposal has already been approved. Please contact the organisers if you need to modify something.")
            return redirect(reverse('proposal_list', kwargs={'camp_slug': self.camp.slug}))

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class EnsureWritableCampMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # do not permit view if camp is in readonly mode
        if self.camp.read_only:
            messages.error(request, "No thanks")
            return redirect(reverse('proposal_list', kwargs={'camp_slug': self.camp.slug}))

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class EnsureUserOwnsProposalMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # make sure that this proposal belongs to the logged in user
        if self.get_object().user.username != request.user.username:
            messages.error(request, "No thanks")
            return redirect(reverse('proposal_list', kwargs={'camp_slug': self.camp.slug}))

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class FileViewMixin(SingleObjectMixin):
    file_field = None
    file_directory_name = None
    object_id_field = None

    def get_directory_name(self):
        return self.file_directory_name

    def get_identifier(self):
        return getattr(self.get_object(), self.object_id_field)

    def get_filename(self):
        file_field = getattr(
            self.get_object(),
            self.file_field
        )
        return os.path.basename(file_field.name)

    def get_path(self):
        return '/public/{directory_name}/{camp_slug}/{identifier}/{filename}'.format(
            directory_name=self.get_directory_name(),
            camp_slug=self.camp.slug,
            identifier=self.get_identifier(),
            filename=self.get_filename()
        )

    def get(self, request, *args, **kwargs):
        path = '{media_root}{file_path}'.format(
            media_root=settings.MEDIA_ROOT,
            file_path=self.get_path()
        )
        return sendfile(request, path)

