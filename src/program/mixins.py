from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import redirect
from django.urls import reverse
from . import models
from django.contrib import messages
import sys, mimetypes
from django.http import Http404, HttpResponse


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


class PictureViewMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # do we have the requested picture?
        if kwargs['picture'] == 'thumbnail':
            if self.get_object().picture_small:
                self.picture = self.get_object().picture_small
            else:
                raise Http404()
        elif kwargs['picture'] == 'large':
            if self.get_object().picture_large:
                self.picture = self.get_object().picture_large
            else:
                raise Http404()
        else:
            # only 'thumbnail' and 'large' pictures supported
            raise Http404()

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)

    def get_picture_response(self):
        if 'runserver' in sys.argv or 'runserver_plus' in sys.argv:
            # this is a local devserver situation, guess mimetype from extension and return picture directly
            response = HttpResponse(self.picture, content_type=mimetypes.types_map[".%s" % self.picture.name.split(".")[-1]])
        else:
            # make nginx serve the picture using X-Accel-Redirect
            # (this works for nginx only, other webservers use x-sendfile)
            # maybe make the header name configurable
            response = HttpResponse()
            response['X-Accel-Redirect'] = '/public/speakerproposals/%(campslug)s/%(proposaluuid)s/%(filename)s' % {
                'campslug': self.camp.slug,
                'proposaluuid': self.get_object().uuid,
                'filename': os.path.basename(self.picture.name),
            }
            response['Content-Type'] = ''
        return response


