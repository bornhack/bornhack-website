from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.views.generic.detail import SingleObjectMixin

if TYPE_CHECKING:
    from django.db.models import Model

logger = logging.getLogger(f"bornhack.{__name__}")


class StaffMemberRequiredMixin:
    """A CBV mixin for when a view should only be permitted for staff users."""

    def dispatch(self, request, *args, **kwargs):
        # only permit staff users
        if not request.user.is_staff:
            messages.error(request, "No thanks")
            raise PermissionDenied

        # continue with the request
        return super().dispatch(request, *args, **kwargs)


class RaisePermissionRequiredMixin(PermissionRequiredMixin):
    """A subclass of PermissionRequiredMixin which raises an exception to return 403 rather than a redirect to the login page
    We use this to avoid a redirect loop since our login page redirects back to the ?next= url when a user is logged in...
    """

    raise_exception = True


class IsTeamPermContextMixin:
    """Mixing for adding is_team_{perm} to context"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perms = self.request.user.get_all_permissions()
        # add bools for each of settings.BORNHACK_TEAM_PERMISSIONS
        for perm in settings.BORNHACK_TEAM_PERMISSIONS:
            # loop over user permissions and set context
            for user_perm in perms:
                if user_perm.startswith("camps.") and user_perm.endswith(
                    f"_team_{perm}",
                ):
                    context[f"is_team_{perm}"] = True
                    break
            else:
                context[f"is_team_{perm}"] = False
        return context


class BaseTeamPermRequiredMixin:
    """Base class for Team<foo>RequiredMixins."""

    perm = None

    def dispatch(self, request, *args, **kwargs):
        user_perms = self.request.user.get_all_permissions()
        for perm in user_perms:
            if perm.endswith(f"_team_{self.perm}"):
                # user has the permission in some team
                return super().dispatch(request, *args, **kwargs)
        messages.error(request, "No thanks")
        raise PermissionDenied


class AnyTeamMemberRequiredMixin(BaseTeamPermRequiredMixin):
    """Mixin for views available to anyone with a "camps.<team>_team_member" permission for any team.

    Currently only used to control backoffice access.
    """

    perm = "member"


class AnyTeamMapperRequiredMixin(BaseTeamPermRequiredMixin):
    """Mixin for views available to anyone with a "camps.<team>_team_mapper" permission for any team.

    Currently only used in backoffice map layer list and create views.
    """

    perm = "mapper"


class AnyTeamFacilitatorRequiredMixin(BaseTeamPermRequiredMixin):
    """Mixin for views available to anyone with a "camps.<team>_team_facilitator" permission for any team.

    Currently only used in backoffice facility list, create, and detail views.
    """

    perm = "facilitator"


class AnyTeamPosRequiredMixin(BaseTeamPermRequiredMixin):
    """Mixin for views available to anyone with a "camps.<team>_team_pos" permission for any team.

    Currently used to control access to the backoffice POS list, POS Transaction List, POS sale list, POS product list, and POS Product Cost List views.
    """

    perm = "pos"


class UserIsObjectOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        return self.get_object().user == self.request.user


class GetObjectMixin(SingleObjectMixin):
    object: Model

    def get_object(self, **kwargs):
        if hasattr(self, "object"):
            return self.object
        return super().get_object(**kwargs)

    def setup(self, request, *args, **kwargs) -> None:
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
