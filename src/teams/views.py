from django.views.generic import ListView

from camps.mixins import CampViewMixin

from .models import Team


class TeamsView(CampViewMixin, ListView):
    template_name = "teams_list.html"
    model = Team
    context_object_name = 'teams'
