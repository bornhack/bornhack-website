from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic.detail import SingleObjectMixin
from teams.models import Team, TeamMember


class EnsureTeamResponsibleMixin(object):
    """
    Use to make sure request.user is responsible for the team specified by kwargs['team_slug']
    """

    def dispatch(self, request, *args, **kwargs):
        self.team = Team.objects.get(slug=kwargs["team_slug"], camp=self.camp)
        if request.user not in self.team.responsible_members.all():
            messages.error(request, "No thanks")
            return redirect(
                "teams:general", camp_slug=self.camp.slug, team_slug=self.team.slug
            )

        return super().dispatch(request, *args, **kwargs)


class EnsureTeamMemberResponsibleMixin(SingleObjectMixin):
    """
    Use to make sure request.user is responsible for the team which TeamMember belongs to
    """

    model = TeamMember

    def dispatch(self, request, *args, **kwargs):
        if request.user not in self.get_object().team.responsible_members.all():
            messages.error(request, "No thanks")
            return redirect(
                "teams:general",
                camp_slug=self.get_object().team.camp.slug,
                team_slug=self.get_object().team.slug,
            )

        return super().dispatch(request, *args, **kwargs)


class TeamViewMixin:
    def get_team(self):
        return self.get_object().team

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.get_team()
        return context
