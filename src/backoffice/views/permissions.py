from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView
from django.views.generic import ListView

from backoffice.forms import ManageTeamPermissionsForm
from backoffice.mixins import OrgaOrTeamLeadViewMixin
from camps.mixins import CampViewMixin
from camps.models import Permission as CampPermission
from teams.models import Team


class TeamPermissionIndexView(OrgaOrTeamLeadViewMixin, ListView):
    model = Team
    template_name = "team_permissions_index.html"

    def setup(self, *args, **kwargs) -> None:
        super().setup(*args, **kwargs)
        # get the teams for which this user can manage permissions
        self.teams = []
        perms = self.request.user.get_all_permissions()
        for team in Team.objects.filter(camp=self.camp):
            if f"camps.{team.slug}_team_lead" in perms or "camps.orga_team_member" in perms:
                # user can manage perms for this team
                if team.approved_members.exists():
                    # there is something to manage
                    self.teams.append(team)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["teams"] = self.teams
        return context


class TeamPermissionManageView(CampViewMixin, FormView):
    """This view is used to see and update team permissions.

    This view does it's own permission checking in setup(),
    so it does not need to inherit from OrgaOrTeamLeadViewMixin.
    """

    template_name = "team_permissions_manage.html"
    form_class = ManageTeamPermissionsForm

    def setup(self, *args, **kwargs) -> None:
        """Get the team object."""
        super().setup(*args, **kwargs)
        self.team = get_object_or_404(
            Team,
            camp=self.camp,
            slug=kwargs["team_slug"],
        )
        # does the user have permission to manage permissions for this team?
        if not self.request.user.has_perm(
            f"camps.{self.team.slug}_team_lead",
        ) and not self.request.user.has_perm("camps.orga_team_member"):
            messages.error(self.request, "No thanks")
            raise PermissionDenied
        self.matrix = {}
        for member in self.team.approved_members.all():
            self.matrix[member.username] = []
            for perm in settings.BORNHACK_TEAM_PERMISSIONS:
                self.matrix[member.username].append(perm)

    def get_form_kwargs(self):
        """Set teams and permissions for the form."""
        kwargs = super().get_form_kwargs()
        kwargs["matrix"] = self.matrix
        return kwargs

    def get_initial(self, *args, **kwargs):
        """Populate the form with current permissions."""
        initial = super().get_initial(*args, **kwargs)
        # loop over users in the matrix
        for member in self.team.approved_members.all():
            # loop over perms and see if user has each
            for perm in settings.BORNHACK_TEAM_PERMISSIONS.keys():
                g = getattr(self.team, f"{perm}_group")
                if member in g.user_set.all():
                    # make checked because the user has this perm
                    initial[f"{member.username}_{perm}"] = True
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.team
        context["perms"] = settings.BORNHACK_TEAM_PERMISSIONS.keys()
        return context

    def form_valid(self, form):
        """Loop over the form fields and add/remove permissions as needed.

        Skipping fields "lead" and "member" as they are handled through memberships.
        """
        # the perms that can be managed through this view
        perms = [perm for perm in settings.BORNHACK_TEAM_PERMISSIONS if perm not in ["lead", "member"]]
        # loop over perms and build a dict for use later
        team_permissions = {}
        permission_content_type = ContentType.objects.get_for_model(CampPermission)
        for perm in perms:
            team_permissions[perm] = Permission.objects.get(
                content_type=permission_content_type,
                codename=f"{self.team.slug}_team_{perm}",
            )
        # loop over form fields
        for field in form.cleaned_data:
            username, perm = field.split("_")
            if username not in self.matrix:
                # no sneaking in new usernames
                continue
            if perm not in perms:
                # no sneaking in unexpected perms
                continue
            user = self.team.members.get(username=username)
            if user.is_superuser:
                # superusers magically have all permissions, nothing to do here
                continue
            g = getattr(self.team, f"{perm}_group")
            if form.cleaned_data[field]:
                g.user_set.add(user)
            else:
                g.user_set.remove(user)
        messages.success(
            self.request,
            f"Updated team permissions for the {self.team.name} Team",
        )
        return redirect(
            reverse(
                "backoffice:team_permission_manage",
                kwargs={"camp_slug": self.camp.slug, "team_slug": self.team.slug},
            ),
        )


class PermissionByUserView(OrgaOrTeamLeadViewMixin, ListView):
    model = User
    template_name = "permissions_by_user.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        permission_content_type = ContentType.objects.get_for_model(CampPermission)
        users = (
            qs.filter(
                user_permissions__isnull=False,
                user_permissions__content_type=permission_content_type,
            )
            | qs.filter(
                groups__permissions__isnull=False,
                groups__permissions__content_type=permission_content_type,
            )
            | qs.filter(is_superuser=True)
        )
        return users.distinct()


class PermissionByPermissionView(OrgaOrTeamLeadViewMixin, ListView):
    model = Permission
    template_name = "permissions_by_permission.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        perms = []
        permission_content_type = ContentType.objects.get_for_model(CampPermission)
        for perm in qs.filter(content_type=permission_content_type):
            perms.append(
                (
                    perm,
                    User.objects.with_perm(
                        perm,
                        backend="django.contrib.auth.backends.ModelBackend",
                    ).exclude(is_superuser=True),
                ),
            )
        return perms


class PermissionByGroupView(OrgaOrTeamLeadViewMixin, ListView):
    model = Group
    template_name = "permissions_by_group.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        permission_content_type = ContentType.objects.get_for_model(CampPermission)
        groups = qs.filter(
            permissions__isnull=False,
            permissions__content_type=permission_content_type,
        )
        return groups.distinct()
