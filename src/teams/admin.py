from django.contrib import admin

from .models import Team, TeamArea, TeamMember

admin.site.register(TeamArea)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_filter = [
        'camp',
    ]

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_filter = [
        'team',
        'approved',
    ]


