from __future__ import annotations

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from camps.mixins import CampViewMixin
from economy.models import Pos
from utils.mixins import RaisePermissionRequiredMixin


class OrgaTeamPermissionMixin(RaisePermissionRequiredMixin):
    """Permission mixin for views used by Orga Team."""

    permission_required = "camps.orga_team_member"


class EconomyTeamPermissionMixin(RaisePermissionRequiredMixin):
    """Permission mixin for views used by Economy Team."""

    permission_required = "camps.economy_team_member"


class InfoTeamPermissionMixin(RaisePermissionRequiredMixin):
    """Permission mixin for views used by Info Team/InfoDesk."""

    permission_required = "camps.info_team_member"


class ContentTeamPermissionMixin(RaisePermissionRequiredMixin):
    """Permission mixin for views used by Content Team."""

    permission_required = "camps.content_team_member"


class GisTeamPermissionMixin(RaisePermissionRequiredMixin):
    """Permission mixin for views used by GIS Team."""

    permission_required = "camps.gis_team_member"


class OrgaOrGisTeamViewMixin(UserPassesTestMixin):
    """A mixin for views that should be accessible only to orga and gis team members."""

    def test_func(self) -> bool:
        """This view requires camps.orga_team_member or camps.gis_team_member permission."""
        if self.request.user.has_perm("camps.orga_team_member"):
            return True
        if self.request.user.has_perm("camps.gis_team_member"):
            return True
        raise PermissionDenied("No thanks")


class PosViewMixin(CampViewMixin, UserPassesTestMixin):
    """A mixin to set self.pos based on pos_slug in url kwargs, and only permit access for users with pos permission for the team."""

    def setup(self, *args, **kwargs) -> None:
        super().setup(*args, **kwargs)
        self.pos = get_object_or_404(
            Pos,
            team__camp=self.camp,
            slug=self.kwargs["pos_slug"],
        )

    def test_func(self) -> bool:
        """This view requires camps.<posteam>_team_pos permission."""
        if self.request.user.has_perm(f"camps.{self.pos.team.slug}_team_pos"):
            return True
        raise PermissionDenied("This PoS user has no permission for this PoS")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["pos"] = self.pos
        return context


class OrgaOrTeamLeadViewMixin(CampViewMixin, UserPassesTestMixin):
    """A mixin for views that should be accessible only to orga and team leads."""

    def test_func(self) -> bool:
        """This view requires camps.orga_team_member or camps.<any team>_team_lead permission."""
        if self.request.user.has_perm("camps.orga_team_member"):
            return True
        for perm in self.request.user.get_all_permissions():
            if perm.startswith("camps.") and perm.endswith("_team_lead"):
                return True
        raise PermissionDenied("No thanks")
