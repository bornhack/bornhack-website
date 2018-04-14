from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from camps.mixins import CampViewMixin
from .models import Team, TeamMember, TeamTask
from .email import add_added_membership_email, add_removed_membership_email
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic.detail import SingleObjectMixin
from django.urls import reverse_lazy
from django.conf import settings
from profiles.models import Profile

import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class EnsureTeamResponsibleMixin(object):
    """
    Use to make sure request.user is responsible for the team specified by kwargs['team_slug']
    """
    def dispatch(self, request, *args, **kwargs):
        self.team = Team.objects.get(slug=kwargs['team_slug'], camp=self.camp)
        if request.user not in self.team.responsible_members.all():
            messages.error(request, 'No thanks')
            return redirect('teams:detail', camp_slug=self.camp.slug, team_slug=self.team.slug)

        return super().dispatch(
            request, *args, **kwargs
        )


class EnsureTeamMemberResponsibleMixin(SingleObjectMixin):
    """
    Use to make sure request.user is responsible for the team which TeamMember belongs to
    """
    model = TeamMember

    def dispatch(self, request, *args, **kwargs):
        if request.user not in self.get_object().team.responsible_members.all():
            messages.error(request, 'No thanks')
            return redirect('teams:detail', camp_slug=self.get_object().team.camp.slug, team_slug=self.get_object().team.slug)

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
    slug_url_kwarg = 'team_slug'

    def get_context_data(self, **kwargs):
        context = super(TeamDetailView, self).get_context_data(**kwargs)
        context['IRCBOT_SERVER_HOSTNAME'] = settings.IRCBOT_SERVER_HOSTNAME
        context['IRCBOT_PUBLIC_CHANNEL'] = settings.IRCBOT_PUBLIC_CHANNEL
        return context


class TeamManageView(CampViewMixin, EnsureTeamResponsibleMixin, UpdateView):
    model = Team
    template_name = "team_manage.html"
    fields = ['description', 'needs_members', 'public_irc_channel_name', 'public_irc_channel_bot', 'public_irc_channel_managed', 'private_irc_channel_name', 'private_irc_channel_bot', 'private_irc_channel_managed']
    slug_url_kwarg = 'team_slug'

    def get_success_url(self):
        return reverse_lazy('teams:detail', kwargs={'camp_slug': self.camp.slug, 'team_slug': self.get_object().slug})

    def form_valid(self, form):
        messages.success(self.request, "Team has been saved")
        return super().form_valid(form)


class TeamJoinView(LoginRequiredMixin, CampViewMixin, UpdateView):
    template_name = "team_join.html"
    model = Team
    fields = []
    slug_url_kwarg = 'team_slug'

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
    slug_url_kwarg = 'team_slug'

    def get(self, request, *args, **kwargs):
        if request.user not in self.get_object().members.all():
            messages.warning(request, "You are not a member of this team")
            return redirect('teams:list', camp_slug=self.get_object().camp.slug)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        TeamMember.objects.filter(team=self.get_object(), user=self.request.user).delete()
        messages.success(self.request, "You are no longer a member of the team %s" % self.get_object().name)
        return redirect('teams:list', camp_slug=self.get_object().camp.slug)



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
        return redirect('teams:detail', camp_slug=self.camp.slug, team_slug=form.instance.team.slug)


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
        return redirect('teams:detail', camp_slug=self.camp.slug, team_slug=form.instance.team.slug)


class TaskDetailView(CampViewMixin, DetailView):
    template_name = "task_detail.html"
    context_object_name = "task"
    model = TeamTask


class TaskCreateView(LoginRequiredMixin, CampViewMixin, EnsureTeamResponsibleMixin, CreateView):
    model = TeamTask
    template_name = "task_form.html"
    fields = ['name', 'description']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.team
        return context

    def form_valid(self, form):
        task = form.save(commit=False)
        task.team = self.team
        if not task.name:
            task.name = "noname"
        task.save()
        return HttpResponseRedirect(task.get_absolute_url())

    def get_success_url(self):
        return self.get_object().get_absolute_url()


class TaskUpdateView(LoginRequiredMixin, CampViewMixin, EnsureTeamResponsibleMixin, UpdateView):
    model = TeamTask
    template_name = "task_form.html"
    fields = ['name', 'description']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.team
        return context

    def form_valid(self, form):
        task = form.save(commit=False)
        task.team = self.team
        if not task.name:
            task.name = "noname"
        task.save()
        return HttpResponseRedirect(task.get_absolute_url())

    def get_success_url(self):
        return self.get_object().get_absolute_url()


class FixIrcAclView(LoginRequiredMixin, CampViewMixin, UpdateView):
    template_name = "fix_irc_acl.html"
    model = Team
    fields = []
    slug_url_kwarg = 'team_slug'

    def dispatch(self, request, *args, **kwargs):
        # we need to call the super().dispatch() method early so self.camp gets populated by CampViewMixin,
        # because the lookups below depend on self.camp being set :)
        response = super().dispatch(
            request, *args, **kwargs
        )

        # check if the logged in user has an approved membership of this team
        if request.user not in self.get_object().approved_members.all():
            messages.error(request, 'No thanks')
            return redirect('teams:detail', camp_slug=self.get_object().camp.slug, team_slug=self.get_object().slug)

        # check if we manage the channel for this team
        if not self.get_object().irc_channel or not self.get_object().irc_channel_managed:
            messages.error(request, 'IRC functionality is disabled for this team, or the team channel is not managed by the bot')
            return redirect('teams:detail', camp_slug=self.get_object().camp.slug, team_slug=self.get_object().slug)

        # check if user has a nickserv username
        if not request.user.profile.nickserv_username:
            messages.error(request, 'Please go to your profile and set your NickServ username first. Make sure the account is registered with NickServ first!')
            return redirect('teams:detail', camp_slug=self.get_object().camp.slug, team_slug=self.get_object().slug)

        return response

    def get(self, request, *args, **kwargs):
        # get membership
        try:
            TeamMember.objects.get(
                user=request.user,
                team=self.get_object(),
                approved=True,
                irc_channel_acl_ok=True
            )
        except TeamMember.DoesNotExist:
            # this membership is already marked as membership.irc_channel_acl_ok=False, no need to do anything
            messages.error(request, 'No need, this membership is already marked as irc_channel_acl_ok=False, so the bot will fix the ACL soon')
            return redirect('teams:detail', camp_slug=self.get_object().camp.slug, team_slug=self.get_object().slug)

        return super().get(
            request, *args, **kwargs
        )


    def form_valid(self, form):
        membership = TeamMember.objects.get(
            user=self.request.user,
            team=self.get_object(),
            approved=True,
            irc_channel_acl_ok=True
        )

        membership.irc_channel_acl_ok = False
        membership.save()
        messages.success(self.request, "OK, hang on while we fix the permissions for your NickServ user '%s' for IRC channel '%s'" % (self.request.user.profile.nickserv_username, form.instance.irc_channel_name))
        return redirect('teams:detail', camp_slug=form.instance.camp.slug, team_slug=form.instance.slug)

