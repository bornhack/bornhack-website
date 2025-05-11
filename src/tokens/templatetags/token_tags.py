from __future__ import annotations

from django import template

from tokens.models import TokenFind

register = template.Library()


@register.filter
def found_by_user(token, user):
    try:
        tokenfind = TokenFind.objects.get(token=token, user=user)
        return tokenfind.created
    except TokenFind.DoesNotExist:
        return False
