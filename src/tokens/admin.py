from __future__ import annotations

from django.contrib import admin

from .models import Token
from .models import TokenFind


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_filter = ["camp", "category", "active"]
    list_display = ["token", "description", "camp", "category", "active", "valid_when"]
    search_fields = ["token", "description", "category"]


@admin.register(TokenFind)
class TokenFindAdmin(admin.ModelAdmin):
    list_filter = ["token__camp", "user"]
    list_display = ["token", "user", "created"]
    search_fields = ["user", "token"]
