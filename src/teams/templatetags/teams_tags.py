from django import template

register = template.Library()


@register.simple_tag
def membershipstatus(user, team):
    return team.memberstatus(user)
