from django.contrib import messages
from django.http import HttpResponseForbidden


class StaffMemberRequiredMixin(object):
    """
    A CBV mixin for when a view should only be permitted for staff users
    """
    def dispatch(self, request, *args, **kwargs):
        # only permit staff users
        if not request.user.is_staff:
            messages.error(request, "No thanks")
            return HttpResponseForbidden()

        # continue with the request
        return super().dispatch(request, *args, **kwargs)

