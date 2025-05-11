import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic import UpdateView

from camps.mixins import CampViewMixin
from profiles.models import Profile

from ..email import add_added_membership_email
from ..email import add_removed_membership_email
from ..models import Team
from ..models import TeamMember
from .mixins import EnsureTeamMemberLeadMixin
from .mixins import TeamViewMixin

logger = logging.getLogger("bornhack.%s" % __name__)


class TeamMembersView(CampViewMixin, DetailView):
    template_name = "team_members.html"
    context_object_name = "team"
    model = Team
    slug_url_kwarg = "team_slug"
    active_menu = "members"


class TeamJoinView(LoginRequiredMixin, CampViewMixin, UpdateView):
    template_name = "team_join.html"
    model = Team
    fields = []
    slug_url_kwarg = "team_slug"
    active_menu = "members"

    def get(self, request, *args, **kwargs):
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

    def form_valid(self, form):
        TeamMember.objects.create(team=self.get_object(), user=self.request.user)
        messages.success(
            self.request,
            "You request to join the team %s has been registered, thank you." % self.get_object().name,
        )
        return redirect("teams:list", camp_slug=self.get_object().camp.slug)


class TeamLeaveView(LoginRequiredMixin, CampViewMixin, UpdateView):
    template_name = "team_leave.html"
    model = Team
    fields = []
    slug_url_kwarg = "team_slug"
    active_menu = "members"

    def get(self, request, *args, **kwargs):
        if request.user not in self.get_object().members.all():
            messages.warning(request, "You are not a member of this team")
            return redirect("teams:list", camp_slug=self.get_object().camp.slug)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        TeamMember.objects.filter(
            team=self.get_object(),
            user=self.request.user,
        ).delete()
        messages.success(
            self.request,
            "You are no longer a member of the team %s" % self.get_object().name,
        )
        return redirect("teams:list", camp_slug=self.get_object().camp.slug)


class TeamMemberRemoveView(
    LoginRequiredMixin,
    TeamViewMixin,
    EnsureTeamMemberLeadMixin,
    UpdateView,
):
    template_name = "teammember_remove.html"
    model = TeamMember
    fields = []
    active_menu = "members"

    def form_valid(self, form):
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
    template_name = "teammember_approve.html"
    model = TeamMember
    fields = []
    active_menu = "members"

    def form_valid(self, form):
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
