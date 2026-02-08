from django import template

from profiles.models import Profile

register = template.Library()

@register.simple_tag(takes_context=True)
def display_name(context, profile: Profile):
    """
    Return the profile display name depending on the users permissions.
    """
    try:
        user = context["request"].user
        camp = context["camp"]
    except KeyError:
        return profile.public_name

    return profile.get_display_name(user, camp)

