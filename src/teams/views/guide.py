from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView

from camps.mixins import CampViewMixin

from ..models import Team


class TeamGuideView(LoginRequiredMixin, CampViewMixin, DetailView):
    template_name = "team_guide.html"
    context_object_name = "team"
    model = Team
    slug_url_kwarg = "team_slug"
    active_menu = "guide"

    def get_queryset(self):
        qs = CampViewMixin.get_queryset(self)
        qs.filter(teammember__approved=True, teammember__user=self.request.user)
        return qs


class TeamGuidePrintView(TeamGuideView):
    template_name = "team_guide_print.html"
