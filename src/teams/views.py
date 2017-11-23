from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, FormView
from camps.mixins import CampViewMixin
from .models import Team, TeamMember, TeamTask
from .forms import ManageTeamForm
from .email import add_added_membership_email, add_removed_membership_email
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.views.generic.detail import SingleObjectMixin
from django.core.urlresolvers import reverse_lazy

from profiles.models import Profile

import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class EnsureTeamResponsibleMixin(SingleObjectMixin):
    model = Team

    def dispatch(self, request, *args, **kwargs):
        if request.user not in self.get_object().responsible.all():
            messages.error(request, 'No thanks')
            return redirect('team_detail', camp_slug=self.camp.slug, slug=self.get_object().slug)

        return super().dispatch(
            request, *args, **kwargs
        )


class TeamListView(CampViewMixin, ListView):
    template_name = "team_list.html"
    model = Team
    context_object_name = 'teams'


class TeamDetailView(CampViewMixin, DetailView):
    template_name = "team_detail.html"
    context_object_name = 'team'
    model = Team


class TeamManageView(CampViewMixin, EnsureTeamResponsibleMixin, UpdateView):
    model = Team
    template_name = "team_manage.html"
    fields = ['description', 'needs_members']

    def get_success_url(self):
        return reverse_lazy('team_detail', kwargs={'camp_slug': self.camp.slug, 'slug': self.get_object().slug})


class TeamJoinView(LoginRequiredMixin, CampViewMixin, UpdateView):
    template_name = "team_join.html"
    model = Team
    fields = []

    def get(self, request, *args, **kwargs):
        if not Profile.objects.get(user=request.user).description:
            messages.warning(
                request,
                "Please fill the description in your profile before joining a team"
            )
            return redirect('teams:list', camp_slug=self.camp.slug)

        if request.user in self.get_object().members.all():
            messages.warning(request, "You are already a member of this team")
            return redirect('teams:list', camp_slug=self.camp.slug)

        if not self.get_object().needs_members:
            messages.warning(request, "This team does not need members right now")
            return redirect('teams:list', camp_slug=self.get_object().camp.slug)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        TeamMember.objects.create(team=self.get_object(), user=self.request.user)
        messages.success(self.request, "You request to join the team %s has been registered, thank you." % self.get_object().name)
        return redirect('teams:list', camp_slug=self.get_object().camp.slug)


class TeamLeaveView(LoginRequiredMixin, CampViewMixin, UpdateView):
    template_name = "team_leave.html"
    model = Team
    fields = []

    def get(self, request, *args, **kwargs):
        if request.user not in self.get_object().members.all():
            messages.warning(request, "You are not a member of this team")
            return redirect('teams:list', camp_slug=self.get_object().camp.slug)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        TeamMember.objects.filter(team=self.get_object(), user=self.request.user).delete()
        messages.success(self.request, "You are no longer a member of the team %s" % self.get_object().name)
        return redirect('teams:list', camp_slug=self.get_object().camp.slug)


class EnsureTeamMemberResponsibleMixin(SingleObjectMixin):
    model = TeamMember

    def dispatch(self, request, *args, **kwargs):
        if request.user not in self.get_object().team.responsible.all():
            messages.error(request, 'No thanks')
            return redirect('team_detail', camp_slug=self.get_object().team.camp.slug, slug=self.get_object().team.slug)

        return super().dispatch(
            request, *args, **kwargs
        )


class TeamMemberRemoveView(LoginRequiredMixin, CampViewMixin, EnsureTeamMemberResponsibleMixin, UpdateView):
    template_name = "teammember_remove.html"
    model = TeamMember
    fields = []

    def form_valid(self, form):
        form.instance.delete()
        if add_removed_membership_email(form.instance):
            messages.success(self.request, "Team member removed")
        else:
            messages.success(self.request, "Team member removed (unable to add email to outgoing queue).")
            logger.error(
                'Unable to add removed email to outgoing queue for teammember: {}'.format(form.instance)
            )
        return redirect('team_detail', camp_slug=self.camp.slug, slug=form.instance.team.slug)


class TeamMemberApproveView(LoginRequiredMixin, CampViewMixin, EnsureTeamMemberResponsibleMixin, UpdateView):
    template_name = "teammember_approve.html"
    model = TeamMember
    fields = []

    def form_valid(self, form):
        form.instance.approved = True
        form.instance.save()
        if add_added_membership_email(form.instance):
            messages.success(self.request, "Team member approved")
        else:
            messages.success(self.request, "Team member removed (unable to add email to outgoing queue).")
            logger.error(
                'Unable to add approved email to outgoing queue for teammember: {}'.format(form.instance)
            )
        return redirect('team_detail', camp_slug=self.camp.slug, slug=form.instance.team.slug)


class TaskDetailView(CampViewMixin, DetailView):
    template_name = "task_detail.html"
    context_object_name = "task"
    model = TeamTask

