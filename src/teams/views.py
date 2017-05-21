from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, FormView
from camps.mixins import CampViewMixin
from .models import Team, TeamMember
from .forms import ManageTeamForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import Http404


class TeamListView(CampViewMixin, ListView):
    template_name = "team_list.html"
    model = Team
    context_object_name = 'teams'


class TeamDetailView(CampViewMixin, DetailView, UpdateView, FormView):
    template_name = "team_detail.html"
    model = Team
    form_class = ManageTeamForm
    context_object_name = 'team'


class TeamJoinView(LoginRequiredMixin, CampViewMixin, UpdateView):
    template_name = "team_join.html"
    model = Team
    fields = []

    def get(self, request, *args, **kwargs):
        if request.user in self.get_object().members.all():
            messages.warning(request, "You are already a member of this team")
            return redirect('team_list', camp_slug=self.camp.slug)

        if not self.get_object().needs_members:
            messages.warning(request, "This team does not need members right now")
            return redirect('team_list', camp_slug=self.get_object().camp.slug)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        TeamMember.objects.create(team=self.get_object(), user=self.request.user)
        messages.success(self.request, "You request to join the team %s has been registered, thank you." % self.get_object().name)
        return redirect('team_list', camp_slug=self.get_object().camp.slug)


class TeamLeaveView(LoginRequiredMixin, CampViewMixin, UpdateView):
    template_name = "team_leave.html"
    model = Team
    fields = []

    def get(self, request, *args, **kwargs):
        if request.user not in self.get_object().members.all():
            messages.warning(request, "You are not a member of this team")
            return redirect('team_list', camp_slug=self.get_object().camp.slug)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        TeamMember.objects.filter(team=self.get_object(), user=self.request.user).delete()
        messages.success(self.request, "You are no longer a member of the team %s" % self.get_object().name)
        return redirect('team_list', camp_slug=self.get_object().camp.slug)
