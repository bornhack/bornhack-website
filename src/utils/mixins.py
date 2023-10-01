import logging

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Model
from django.views.generic.detail import SingleObjectMixin
from django.views.generic import CreateView
from django.views.generic import UpdateView

logger = logging.getLogger("bornhack.%s" % __name__)


class StaffMemberRequiredMixin:
    """
    A CBV mixin for when a view should only be permitted for staff users
    """

    def dispatch(self, request, *args, **kwargs):
        # only permit staff users
        if not request.user.is_staff:
            messages.error(request, "No thanks")
            raise PermissionDenied()

        # continue with the request
        return super().dispatch(request, *args, **kwargs)


class RaisePermissionRequiredMixin(PermissionRequiredMixin):
    """
    A subclass of PermissionRequiredMixin which raises an exception to return 403 rather than a redirect to the login page
    We use this to avoid a redirect loop since our login page redirects back to the ?next= url when a user is logged in...
    """

    raise_exception = True


class UserIsObjectOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        return self.get_object().user == self.request.user


class GetObjectMixin(SingleObjectMixin):
    object: Model

    def get_object(self, **kwargs):
        if hasattr(self, "object"):
            return self.object
        return super().get_object(**kwargs)

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()


class VerbView:
    """Base class for VerbCreateView and VerbUpdateView."""
    verb = "UnknownVerb"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["verb"] = self.verb
        return context


class VerbCreateView(VerbView, CreateView):
    """Subclass of CreateView where self.verb is set for use in headlines and form buttons."""
    verb = "Create"


class VerbUpdateView(VerbView, UpdateView):
    """Subclass of UpdateView where self.verb is set for use in headlines and form buttons."""
    verb = "Update"
