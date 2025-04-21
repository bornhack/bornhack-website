from utils.mixins import RaisePermissionRequiredMixin
from camps.mixins import CampViewMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.detail import SingleObjectMixin

from teams.models import Team
from teams.models import TeamMember


class EnsureTeamLeadMixin:
    """Use to make sure request.user has team lead permission for the team specified by kwargs['team_slug']"""

    def dispatch(self, request, *args, **kwargs):
        self.team = Team.objects.get(slug=kwargs["team_slug"], camp=self.camp)
        if self.team.lead_permission_set not in request.user.get_all_permissions():
            messages.error(request, "No thanks")
            return redirect(
                "teams:general",
                camp_slug=self.camp.slug,
                team_slug=self.team.slug,
            )

        return super().dispatch(request, *args, **kwargs)


class EnsureTeamMemberLeadMixin(SingleObjectMixin):
    """Use to make sure request.user has team lead permission for the team which TeamMember belongs to"""

    model = TeamMember

    def dispatch(self, request, *args, **kwargs):
        if (
            self.get_object().team.lead_permission_set
            not in request.user.get_all_permissions()
        ):
            messages.error(request, "No thanks")
            return redirect(
                "teams:general",
                camp_slug=self.get_object().team.camp.slug,
                team_slug=self.get_object().team.slug,
            )

        return super().dispatch(request, *args, **kwargs)


class TeamViewMixin(CampViewMixin):
    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.team = Team.objects.get(slug=kwargs["team_slug"], camp=self.camp)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.team
        return context


class TeamInfopagerPermissionMixin(RaisePermissionRequiredMixin):
    """Permission mixin for views restricted to users with infopager permission for self.team"""

    def get_permission_required(self):
        return [self.team.infopager_permission_set]


class TeamTaskerPermissionMixin(RaisePermissionRequiredMixin):
    """Permission mixin for views restricted to users with tasker permission for self.team"""

    def get_permission_required(self):
        return [self.team.tasker_permission_set]
