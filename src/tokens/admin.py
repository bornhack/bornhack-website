from django.contrib import admin
from .models import Token, TokenFind


@admin.register(Token)
class InfoCategorydmin(admin.ModelAdmin):
    list_filter = ["camp"]
    list_display = ["token", "description", "camp"]
    search_fields = ["token", "description"]


@admin.register(TokenFind)
class InfoCategorydmin(admin.ModelAdmin):
    list_filter = ["token__camp", "user"]
    list_display = ["token", "user", "created"]
    search_fields = ["user", "token"]
