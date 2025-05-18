"""Views for the guide of the teams application."""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import DetailView

from camps.mixins import CampViewMixin
from teams.models import Team
from teams.models import TeamMember
from utils.mixins import IsPermissionMixin


class TeamGuideView(LoginRequiredMixin, CampViewMixin, UserPassesTestMixin, IsPermissionMixin, DetailView):
    """View for the team guide."""
    template_name = "team_guide.html"
    context_object_name = "team"
    model = Team
    slug_url_kwarg = "team_slug"
    active_menu = "guide"

    def test_func(self) -> bool:
        """Method to test if the user is approved for this team."""
        try:
            TeamMember.objects.get(
                user=self.request.user,
                team=self.get_object(),
                approved=True,
            )
        except TeamMember.DoesNotExist:
            return False
        else:
            return True


class TeamGuidePrintView(TeamGuideView):
    """View for printing the team guide.

    Includes permissions from TeamGuideView
    """
    template_name = "team_guide_print.html"
