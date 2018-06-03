from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib import messages
from camps.models import Camp


class BackofficeViewMixin(object):
    def dispatch(self, request, *args, **kwargs):
        # only permit staff users
        if not request.user.is_staff:
            messages.error(request, "No thanks")
            return HttpResponseForbidden()

        # get camp from url kwarg
        self.bocamp = get_object_or_404(Camp, slug=kwargs['bocamp_slug'])

        # continue with the request
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ Add Camp to template context """
        context = super().get_context_data(**kwargs)
        context['bocamp'] = self.bocamp
        return context

