from django import template
from django.utils.safestring import mark_safe

from teams.models import TeamMember

register = template.Library()


@register.filter
def is_team_member(user, team):
    return TeamMember.objects.filter(team=team, user=user, approved=True).exists()


@register.simple_tag
def membershipstatus(user, team, showicon=False):
    if user in team.leads.all():
        text = "Lead"
        icon = "fa-star"
    elif user in team.approved_members.all():
        text = "Member"
        icon = "fa-thumbs-o-up"
    elif user in team.unapproved_members.all():
        text = "Membership pending approval"
        icon = "fa-clock-o"
    else:
        text = "Not member"
        icon = "fa-times"

    if showicon:
        return mark_safe(f"<i class='fa {icon}' title='{text}'></i>")
    return text
