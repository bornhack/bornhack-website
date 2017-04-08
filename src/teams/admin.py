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


