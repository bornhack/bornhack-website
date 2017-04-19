from django.contrib import admin
from .models import Team, TeamArea, TeamMember
from .email import send_add_membership_email, send_remove_membership_email

admin.site.register(TeamArea)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    def get_responsible(self, obj):
        return ", ".join([resp.get_full_name() for resp in obj.responsible])
    get_responsible.short_description = 'Responsible'

    list_display = [
        'name',
        'area',
        'get_responsible',
        'needs_members',
    ]

    list_filter = [
        'camp',
        'needs_members',
    ]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_filter = [
        'team',
        'approved',
    ]

    actions = ['approve_membership', 'remove_member']

    def approve_membership(self, request, queryset):
        teams_count = queryset.values('team').distinct().count()
        updated = 0

        for membership in queryset:
            membership.approved = True
            membership.save()
            updated += 1
            send_add_membership_email(membership)

        self.message_user(
            request,
            'Membership(s) approved: Added {} user(s) to {} team(s).'.format(
                updated,
                teams_count
            )
        )
    approve_membership.description = 'Approve membership.'

    def remove_member(self, request, queryset):
        teams_count = queryset.values('team').distinct().count()
        updated = 0

        for membership in queryset:
            send_remove_membership_email(membership)
            membership.delete()
            updated += 1

        self.message_user(
            request,
            'Removed {} user(s) from {} team(s).'.format(
                updated,
                teams_count
            )
        )
    remove_member.description = 'Remove a user from the team.'

