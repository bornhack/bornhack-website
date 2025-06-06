"""All Django admin views for application token."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import ClassVar

from django.contrib import admin

from .models import Token
from .models import TokenFind


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    """Django admin for tokens."""

    list_filter: ClassVar[list[str]] = ["camp", "hint", "active"]
    list_display: ClassVar[list[str]] = ["token", "description", "camp", "hint", "active", "valid_when"]
    search_fields: ClassVar[list[str]] = ["token", "description", "hint"]


@admin.register(TokenFind)
class TokenFindAdmin(admin.ModelAdmin):
    """Django admin for token finds."""

    list_filter: ClassVar[list[str]] = ["token__camp", "user"]
    list_display: ClassVar[list[str]] = ["token", "user", "created"]
    search_fields: ClassVar[list[str]] = ["user", "token"]
