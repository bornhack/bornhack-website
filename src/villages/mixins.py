from django.views.generic.detail import SingleObjectMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class EnsureWritableCampMixin(SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        # do not permit view if camp is in readonly mode
        if self.camp.read_only:
            messages.error(request, "No thanks")
            return redirect(
                reverse("village_list", kwargs={"camp_slug": self.camp.slug})
            )

        # alright, continue with the request
        return super().dispatch(request, *args, **kwargs)
