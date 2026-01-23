"""Base view for teams."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.edit import UpdateView

from camps.mixins import CampViewMixin
from phonebook.models import DectRegistration
from teams.models import Team
from teams.models import TeamMember
from utils.mixins import IsTeamPermContextMixin
from utils.widgets import MarkdownWidget

from .mixins import EnsureTeamLeadMixin

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.forms import Form
    from django.http import HttpRequest
    from django.http import HttpResponse
    from django.http import HttpResponseRedirect

logger = logging.getLogger(f"bornhack.{__name__}")


class TeamListView(CampViewMixin, ListView):
    """View for the list of teams."""

    template_name = "team_list.html"
    model = Team
    context_object_name = "teams"

    def get_queryset(self, *args, **kwargs) -> QuerySet:
        """Method for prefetching team members."""
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("members")
        return qs.prefetch_related("members__profile")
        # TODO(tyk): there is more to be gained here but the templatetag we use to see if
        # the logged-in user is a member of the current team does not benefit from the prefetching,
        # also the getting of team leads and their profiles do not use the prefetching
        # :( /tyk

    def get_context_data(self, *, object_list: list | None = None, **kwargs) -> dict:
        """Method for adding user_teams to the context."""
        context = super().get_context_data(object_list=object_list, **kwargs)
        if self.request.user.is_authenticated:
            context["user_teams"] = self.request.user.teammember_set.filter(
                team__camp=self.camp,
            )
        return context


class TeamGeneralView(CampViewMixin, IsTeamPermContextMixin, DetailView):
    """General view for a team."""

    template_name = "team_general.html"
    context_object_name = "team"
    model = Team
    slug_url_kwarg = "team_slug"
    active_menu = "general"

    def get_context_data(self, **kwargs) -> dict:
        """Method for adding ircbot info to context."""
        context = super().get_context_data(**kwargs)
        context["IRCBOT_SERVER_HOSTNAME"] = settings.IRCBOT_SERVER_HOSTNAME
        context["IRCBOT_PUBLIC_CHANNEL"] = settings.IRCBOT_PUBLIC_CHANNEL
        return context


class TeamSettingsView(CampViewMixin, EnsureTeamLeadMixin, IsTeamPermContextMixin, UpdateView):
    """View for mananaging team members."""

    model = Team
    template_name = "team_settings.html"
    fields = (
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
        "public_phone_number",
        "public_dect_number",
        "guide",
    )
    slug_url_kwarg = "team_slug"
    active_menu = "settings"

    def get_form(self, *args, **kwargs) -> Form:
        """Method for updating form widgets."""
        form = super().get_form(*args, **kwargs)
        form.fields["guide"].widget = MarkdownWidget()

        dect_filter = DectRegistration.objects.filter(
            camp=self.camp,
            user__in=self.object.members.all()
        )
        form.fields["public_dect_number"].queryset = dect_filter.filter(
            publish_in_phonebook=True
        )

        return form

    def get_success_url(self) -> str:
        """Method for returning the success url."""
        kwargs = {
            "camp_slug": self.camp.slug,
            "team_slug": self.get_object().slug
        }
        return reverse_lazy("teams:general", kwargs=kwargs)

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """Method for sending success message if form is valid."""
        messages.success(self.request, "Team has been saved")
        return super().form_valid(form)


class FixIrcAclView(LoginRequiredMixin, CampViewMixin, IsTeamPermContextMixin, UpdateView):
    """View for fixing IRC ACL's."""

    template_name = "fix_irc_acl.html"
    model = Team
    fields = ()
    slug_url_kwarg = "team_slug"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Method dispatch."""
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
                "Please go to your profile and set your NickServ username first. "
                "Make sure the account is registered with NickServ first!",
            )
            return redirect(
                "teams:general",
                camp_slug=self.get_object().camp.slug,
                team_slug=self.get_object().slug,
            )

        return response

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Get membership."""
        try:
            TeamMember.objects.get(
                user=request.user,
                team=self.get_object(),
                approved=True,
                irc_channel_acl_ok=True,
            )
        except TeamMember.DoesNotExist:
            messages.error(
                request,
                "No need, this membership is already marked as irc_channel_acl_ok=False, "
                "so the bot will fix the ACL soon",
            )
            return redirect(
                "teams:general",
                camp_slug=self.get_object().camp.slug,
                team_slug=self.get_object().slug,
            )

        return super().get(request, *args, **kwargs)

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """Method for adding membership and returning a message."""
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
            f"OK, hang on while we fix the permissions for your NickServ user "
            f"'{self.request.user.profile.nickserv_username}' for IRC channel '{form.instance.irc_channel_name}'",
        )
        return redirect(
            "teams:general",
            camp_slug=form.instance.camp.slug,
            team_slug=form.instance.slug,
        )
