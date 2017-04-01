from django.views.generic import ListView, DetailView

from camps.mixins import CampViewMixin

from .models import Team


class TeamListView(CampViewMixin, ListView):
    template_name = "team_list.html"
    queryset = Team.objects.filter(sub_team_of=None)
    context_object_name = 'teams'


class TeamDetailView(CampViewMixin, DetailView):
    template_name = "team_detail.html"
    model = Team
    context_object_name = 'team'
