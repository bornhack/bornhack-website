"""Django admin for teams."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import ClassVar

    from django.db.models import QuerySet
    from django.http import HttpRequest

from django.contrib import admin

from camps.utils import CampPropertyListFilter

from .email import add_added_membership_email
from .email import add_removed_membership_email
from .models import Team
from .models import TeamMember
from .models import TeamShift
from .models import TeamTask


@admin.register(TeamTask)
class TeamTaskAdmin(admin.ModelAdmin):
    """Django admin for team tasks."""
    list_display: ClassVar[list[str]] = ["id", "team", "name", "description"]


class TeamMemberInline(admin.TabularInline):
    """Django admin inline field for team member."""
    model = TeamMember


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Django admin for teams."""
    save_as = True

    @admin.display(
        description="Leads",
    )
    def get_leads(self, obj: Team) -> str:
        """Method to return team leads."""
        return ", ".join(
            [lead.profile.public_credit_name for lead in obj.leads.all()],
        )

    list_display: ClassVar[list[str]] = [
        "name",
        "camp",
        "get_leads",
        "needs_members",
        "public_irc_channel_name",
        "public_irc_channel_bot",
        "public_irc_channel_managed",
        "private_irc_channel_name",
        "private_irc_channel_bot",
        "private_irc_channel_managed",
    ]

    list_filter: ClassVar[list[str]] = [
        CampPropertyListFilter,
        "needs_members",
        "public_irc_channel_bot",
        "public_irc_channel_managed",
        "private_irc_channel_bot",
        "private_irc_channel_managed",
    ]
    inlines: ClassVar[list] = [TeamMemberInline]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Django admin for team members."""
    list_filter: ClassVar[list] = [CampPropertyListFilter, "team", "approved"]

    actions: ClassVar[list[str]] = ["approve_membership", "remove_member"]

    def approve_membership(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Method for approving team membership status."""
        teams_count = queryset.values("team").distinct().count()
        updated = 0

        for membership in queryset:
            membership.approved = True
            membership.save()
            updated += 1
            add_added_membership_email(membership)

        self.message_user(
            request,
            f"Membership(s) approved: Added {updated} user(s) to {teams_count} team(s).",
        )

    approve_membership.description = "Approve membership."

    def remove_member(self, request: HttpRequest, queryset: QuerySet) -> None:
        """Method for removing team membership status."""
        teams_count = queryset.values("team").distinct().count()
        updated = 0

        for membership in queryset:
            add_removed_membership_email(membership)
            membership.delete()
            updated += 1

        self.message_user(
            request,
            f"Removed {updated} user(s) from {teams_count} team(s).",
        )

    remove_member.description = "Remove a user from the team."


@admin.register(TeamShift)
class TeamShiftAdmin(admin.ModelAdmin):
    """Django admin for team shifts."""
    list_filter: ClassVar[list[str]] = ["team"]
