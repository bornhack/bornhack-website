from django.contrib import admin

from .models import Team, TeamArea, TeamMember

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

    actions = ['add_member', 'remove_member']

    def add_member(self, request, queryset):
        teams_count = queryset.values('team').distinct().count()
        rows_updated = queryset.update(approved=True)
        self.message_user(
            request,
            'Added {} user(s) to {} team(s).'.format(
                rows_updated,
                teams_count
            )
        )
    add_member.description = 'Add a user to the team.'

    def remove_member(self, request, queryset):
        teams_count = queryset.values('team').distinct().count()
        users_removed = queryset.delete()[0]
        self.message_user(
            request,
            'Removed {} user(s) from {} team(s).'.format(
                users_removed,
                teams_count
            )
        )
    remove_member.description = 'Remove a user from the team.'
