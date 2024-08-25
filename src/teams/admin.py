from __future__ import annotations

from typing import TYPE_CHECKING

from camps.utils import CampPropertyListFilter
from django.contrib import admin

from .email import add_added_membership_email
from .email import add_removed_membership_email
from .models import Team
from .models import TeamMember
from .models import TeamShift
from .models import TeamTask

if TYPE_CHECKING:
    from django.http import HttpRequest


@admin.register(TeamTask)
class TeamTaskAdmin(admin.ModelAdmin):
    list_display = ["id", "team", "name", "description"]


class TeamMemberInline(admin.TabularInline):
    model = TeamMember


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    save_as = True

    @admin.display(
        description="Responsible",
    )
    def get_responsible(self, obj):
        return ", ".join(
            [resp.profile.public_credit_name for resp in obj.responsible_members.all()],
        )

    list_display = [
        "name",
        "camp",
        "get_responsible",
        "needs_members",
        "public_irc_channel_name",
        "public_irc_channel_bot",
        "public_irc_channel_managed",
        "private_irc_channel_name",
        "private_irc_channel_bot",
        "private_irc_channel_managed",
    ]

    list_filter = [
        CampPropertyListFilter,
        "needs_members",
        "public_irc_channel_bot",
        "public_irc_channel_managed",
        "private_irc_channel_bot",
        "private_irc_channel_managed",
    ]
    inlines = [TeamMemberInline]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_filter = [CampPropertyListFilter, "team", "approved"]

    actions = ["approve_membership", "remove_member"]

    def approve_membership(self, request: HttpRequest, queryset) -> None:
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

    def remove_member(self, request: HttpRequest, queryset) -> None:
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
    list_filter = ["team"]
