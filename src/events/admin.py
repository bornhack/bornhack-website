from __future__ import annotations

from django.contrib import admin

from .models import Routing
from .models import Type


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Routing)
class RoutingAdmin(admin.ModelAdmin):
    pass
