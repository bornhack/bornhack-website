import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.edit import UpdateView

from camps.mixins import CampViewMixin
from utils.widgets import MarkdownWidget

from ..models import Team
from ..models import TeamMember
from .mixins import EnsureTeamLeadMixin

logger = logging.getLogger("bornhack.%s" % __name__)


class TeamListView(CampViewMixin, ListView):
    template_name = "team_list.html"
    model = Team
    context_object_name = "teams"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("members")
        qs = qs.prefetch_related("members__profile")
        # FIXME: there is more to be gained here but the templatetag we use to see if
        # the logged-in user is a member of the current team does not benefit from the prefetching,
        # also the getting of team leads and their profiles do not use the prefetching
        # :( /tyk
        return qs

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        if self.request.user.is_authenticated:
            context["user_teams"] = self.request.user.teammember_set.filter(
                team__camp=self.camp,
            )
        return context


class TeamGeneralView(CampViewMixin, DetailView):
    template_name = "team_general.html"
    context_object_name = "team"
    model = Team
    slug_url_kwarg = "team_slug"
    active_menu = "general"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["IRCBOT_SERVER_HOSTNAME"] = settings.IRCBOT_SERVER_HOSTNAME
        context["IRCBOT_PUBLIC_CHANNEL"] = settings.IRCBOT_PUBLIC_CHANNEL
        return context


class TeamManageView(CampViewMixin, EnsureTeamLeadMixin, UpdateView):
    model = Team
    template_name = "team_manage.html"
    fields = [
        "description",
        "needs_members",
        "public_irc_channel_name",
        "public_irc_channel_bot",
        "public_irc_channel_managed",
        "private_irc_channel_name",
        "private_irc_channel_bot",
        "private_irc_channel_managed",
        "public_signal_channel_link",
        "private_signal_channel_link",
        "guide",
    ]
    slug_url_kwarg = "team_slug"

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["guide"].widget = MarkdownWidget()
        return form

    def get_success_url(self):
        return reverse_lazy(
            "teams:general",
            kwargs={"camp_slug": self.camp.slug, "team_slug": self.get_object().slug},
        )

    def form_valid(self, form):
        messages.success(self.request, "Team has been saved")
        return super().form_valid(form)


class FixIrcAclView(LoginRequiredMixin, CampViewMixin, UpdateView):
    template_name = "fix_irc_acl.html"
    model = Team
    fields = []
    slug_url_kwarg = "team_slug"

    def dispatch(self, request, *args, **kwargs):
        # we need to call the super().dispatch() method early so self.camp gets populated by CampViewMixin,
        # because the lookups below depend on self.camp being set :)
        response = super().dispatch(request, *args, **kwargs)

        # check if the logged in user has an approved membership of this team
        if request.user not in self.get_object().approved_members.all():
            messages.error(request, "No thanks")
            return redirect(
                "teams:general",
                camp_slug=self.get_object().camp.slug,
                team_slug=self.get_object().slug,
            )

        # check if we manage the channel for this team
        if not self.get_object().irc_channel or not self.get_object().irc_channel_managed:
            messages.error(
                request,
                "IRC functionality is disabled for this team, or the team channel is not managed by the bot",
            )
            return redirect(
                "teams:general",
                camp_slug=self.get_object().camp.slug,
                team_slug=self.get_object().slug,
            )

        # check if user has a nickserv username
        if not request.user.profile.nickserv_username:
            messages.error(
                request,
                "Please go to your profile and set your NickServ username first. Make sure the account is registered with NickServ first!",
            )
            return redirect(
                "teams:general",
                camp_slug=self.get_object().camp.slug,
                team_slug=self.get_object().slug,
            )

        return response

    def get(self, request, *args, **kwargs):
        # get membership
        try:
            TeamMember.objects.get(
                user=request.user,
                team=self.get_object(),
                approved=True,
                irc_channel_acl_ok=True,
            )
        except TeamMember.DoesNotExist:
            # this membership is already marked as membership.irc_channel_acl_ok=False, no need to do anything
            messages.error(
                request,
                "No need, this membership is already marked as irc_channel_acl_ok=False, so the bot will fix the ACL soon",
            )
            return redirect(
                "teams:general",
                camp_slug=self.get_object().camp.slug,
                team_slug=self.get_object().slug,
            )

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        membership = TeamMember.objects.get(
            user=self.request.user,
            team=self.get_object(),
            approved=True,
            irc_channel_acl_ok=True,
        )

        membership.irc_channel_acl_ok = False
        membership.save()
        messages.success(
            self.request,
            "OK, hang on while we fix the permissions for your NickServ user '%s' for IRC channel '%s'"
            % (
                self.request.user.profile.nickserv_username,
                form.instance.irc_channel_name,
            ),
        )
        return redirect(
            "teams:general",
            camp_slug=form.instance.camp.slug,
            team_slug=form.instance.slug,
        )
