"""Views for team members."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic import UpdateView

from camps.mixins import CampViewMixin
from profiles.models import Profile
from teams.email import add_added_membership_email
from teams.email import add_removed_membership_email
from teams.models import Team
from teams.models import TeamMember
from utils.mixins import IsTeamPermContextMixin

from .mixins import EnsureTeamMemberLeadMixin
from .mixins import TeamViewMixin

if TYPE_CHECKING:
    from django.forms import Form
    from django.http import HttpRequest
    from django.http import HttpResponse
    from django.http import HttpResponseRedirect

logger = logging.getLogger(f"bornhack.{__name__}")


class TeamMembersView(CampViewMixin, IsTeamPermContextMixin, DetailView):
    """List view for team members."""
    template_name = "team_members.html"
    context_object_name = "team"
    model = Team
    slug_url_kwarg = "team_slug"
    active_menu = "members"


class TeamJoinView(LoginRequiredMixin, CampViewMixin, UpdateView):
    """View displayed when joining a team."""
    template_name = "team_join.html"
    model = Team
    fields = ()
    slug_url_kwarg = "team_slug"
    active_menu = "members"

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Get method view."""
        if not Profile.objects.get(user=request.user).description:
            messages.warning(
                request,
                "Please fill the description in your profile before joining a team",
            )
            return redirect("teams:list", camp_slug=self.camp.slug)

        if request.user in self.get_object().members.all():
            messages.warning(request, "You are already a member of this team")
            return redirect("teams:list", camp_slug=self.camp.slug)

        if not self.get_object().needs_members:
            messages.warning(request, "This team does not need members right now")
            return redirect("teams:list", camp_slug=self.get_object().camp.slug)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """Method to create team member and show message."""
        TeamMember.objects.create(team=self.get_object(), user=self.request.user)
        messages.success(
            self.request,
            f"You request to join the team {self.get_object().name} has been registered, thank you.",
        )
        return redirect("teams:list", camp_slug=self.get_object().camp.slug)


class TeamLeaveView(LoginRequiredMixin, CampViewMixin, UpdateView):
    """View for leaving a team."""
    template_name = "team_leave.html"
    model = Team
    fields = ()
    slug_url_kwarg = "team_slug"
    active_menu = "members"

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Get method for leaving a team."""
        if request.user not in self.get_object().members.all():
            messages.warning(request, "You are not a member of this team")
            return redirect("teams:list", camp_slug=self.get_object().camp.slug)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """Method deletes team member."""
        TeamMember.objects.filter(
            team=self.get_object(),
            user=self.request.user,
        ).delete()
        messages.success(
            self.request,
            f"You are no longer a member of the team {self.get_object().name}",
        )
        return redirect("teams:list", camp_slug=self.get_object().camp.slug)


class TeamMemberRemoveView(
    LoginRequiredMixin,
    TeamViewMixin,
    EnsureTeamMemberLeadMixin,
    UpdateView,
):
    """View for removing a team member."""
    template_name = "teammember_remove.html"
    model = TeamMember
    fields = ()
    active_menu = "members"

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """Method to delete instance and show message.."""
        form.instance.delete()
        if add_removed_membership_email(form.instance):
            messages.success(self.request, "Team member removed")
        else:
            messages.success(
                self.request,
                "Team member removed (unable to add email to outgoing queue).",
            )
            logger.error(
                f"Unable to add removed email to outgoing queue for teammember: {form.instance}",
            )
        return redirect(
            "teams:general",
            camp_slug=self.camp.slug,
            team_slug=form.instance.team.slug,
        )


class TeamMemberApproveView(
    LoginRequiredMixin,
    TeamViewMixin,
    EnsureTeamMemberLeadMixin,
    UpdateView,
):
    """View to approve team member."""
    template_name = "teammember_approve.html"
    model = TeamMember
    fields = ()
    active_menu = "members"

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """Method to set approve true and show message.."""
        form.instance.approved = True
        form.instance.save()
        if add_added_membership_email(form.instance):
            messages.success(self.request, "Team member approved")
        else:
            messages.success(
                self.request,
                "Team member removed (unable to add email to outgoing queue).",
            )
            logger.error(
                f"Unable to add approved email to outgoing queue for teammember: {form.instance}",
            )
        return redirect(
            "teams:general",
            camp_slug=self.camp.slug,
            team_slug=form.instance.team.slug,
        )
