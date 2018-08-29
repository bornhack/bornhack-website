from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import PermissionRequiredMixin


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


class RaisePermissionRequiredMixin(PermissionRequiredMixin):
    """
    A subclass of PermissionRequiredMixin which raises an exception to return 403 rather than a redirect to the login page
    We use this to avoid a redirect loop since our login page redirects back to the ?next= url when a user is logged in...
    """
    raise_exception = True

