from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from camps.mixins import CampViewMixin
from economy.models import Pos
from utils.mixins import RaisePermissionRequiredMixin


class OrgaTeamPermissionMixin(RaisePermissionRequiredMixin):
    """
    Permission mixin for views used by Orga Team
    """

    permission_required = ("camps.backoffice_permission", "camps.orgateam_permission")


class EconomyTeamPermissionMixin(RaisePermissionRequiredMixin):
    """
    Permission mixin for views used by Economy Team
    """

    permission_required = (
        "camps.backoffice_permission",
        "camps.economyteam_permission",
    )


class InfoTeamPermissionMixin(RaisePermissionRequiredMixin):
    """
    Permission mixin for views used by Info Team/InfoDesk
    """

    permission_required = ("camps.backoffice_permission", "camps.infoteam_permission")


class ContentTeamPermissionMixin(RaisePermissionRequiredMixin):
    """
    Permission mixin for views used by Content Team
    """

    permission_required = (
        "camps.backoffice_permission",
        "camps.contentteam_permission",
    )


class PosViewMixin(CampViewMixin, UserPassesTestMixin):
    """A mixin to set self.pos based on pos_slug in url kwargs."""

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.pos = get_object_or_404(
            Pos,
            team__camp=self.camp,
            slug=self.kwargs["pos_slug"],
        )

    def test_func(self):
        """
        This view requires two permissions, camps.backoffice_permission and the permission_set for the team in question.
        """
        if not self.pos.team.permission_set:
            raise PermissionDenied("No permissions set defined for this team")
        if not self.request.user.has_perm("camps.backoffice_permission"):
            raise PermissionDenied("User has no backoffice permission")

        if not self.request.user.has_perm(
            "camps.orgateam_permission",
        ) and not self.request.user.has_perm("camps." + self.pos.team.permission_set):
            raise PermissionDenied("User has no permission for this Pos")
        return True

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["pos"] = self.pos
        return context
