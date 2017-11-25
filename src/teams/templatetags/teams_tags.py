from django import template
from teams.models import TeamMember

register = template.Library()


@register.simple_tag
def membershipstatus(user, team):
    return team.memberstatus(user)

@register.filter
def is_team_member(user, team):
    return TeamMember.objects.filter(team=team, user=user, approved=True).exists()
