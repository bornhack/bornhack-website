"""Token template tags for the Token application."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django import template

from tokens.models import TokenFind

if TYPE_CHECKING:
    from django.contrib.auth.models import User

register = template.Library()


@register.filter
def found_by_user(token: str, user: User) -> bool:
    """Template tag to show if the token is found."""
    try:
        tokenfind = TokenFind.objects.get(token=token, user=user)
    except TokenFind.DoesNotExist:
        return False
    else:
        return tokenfind.created
