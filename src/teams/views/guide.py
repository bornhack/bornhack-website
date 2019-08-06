from django.views.generic import DetailView

from camps.mixins import CampViewMixin
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

from ..models import Team, TeamMember


class TeamGuideView(LoginRequiredMixin, CampViewMixin, UserPassesTestMixin, DetailView):
    template_name = "team_guide.html"
    context_object_name = "team"
    model = Team
    slug_url_kwarg = "team_slug"
    active_menu = "guide"

    def test_func(self):
        # Make sure that the user is an approved member of the team
        try:
            TeamMember.objects.get(
                user=self.request.user, team=self.get_object(), approved=True
            )
        except TeamMember.DoesNotExist:
            return False
        else:
            return True


class TeamGuidePrintView(TeamGuideView):
    template_name = "team_guide_print.html"
