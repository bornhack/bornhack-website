from django.contrib import admin

from .models import Routing, Type


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Routing)
class RoutingAdmin(admin.ModelAdmin):
    pass
