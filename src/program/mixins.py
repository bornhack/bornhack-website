from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import redirect
from django.urls import reverse
from . import models


class CreateUserSubmissionMixin(SingleObjectMixin):
    def form_valid(self, form):
        # set camp and user before saving
        form.instance.camp = self.camp
        form.instance.user = self.request.user
        speaker = form.save()
        return redirect(reverse('submission_list', kwargs={'camp_slug': self.camp.slug}))


class EnsureUnpprovedSubmissionMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # do not permit editing if the submission is already approved
        if self.get_object().submission_status == models.UserSubmittedModel.SUBMISSION_APPROVED:
            messages.error(request, "This submission has already been approved. Please contact the organisers if you need to modify something." % self.camp.title)
            return redirect(reverse('submissions_list', kwargs={'camp_slug': self.camp.slug}))

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)


class EnsureUserOwnsSubmissionMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # make sure that this submission belongs to the logged in user
        if self.get_object().user.username != request.user.username:
            messages.error(request, "No thanks")
            return redirect(reverse('submissions_list', kwargs={'camp_slug': self.camp.slug}))

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)

