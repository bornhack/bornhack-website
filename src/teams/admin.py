from django.contrib import admin

from .models import Team, TeamArea, TeamMember

admin.site.register(Team)
admin.site.register(TeamArea)
admin.site.register(TeamMember)

