"""Maps Django Admin."""

from __future__ import annotations

from typing import ClassVar

from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin

from .models import ExternalLayer
from .models import Feature
from .models import Group
from .models import Layer
from .models import UserLocation
from .models import UserLocationType


@admin.register(Feature)
class FeatureAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    """Feature Admin."""

    display_raw = True
    save_as = True
    list_display: ClassVar[list[str]] = [
        "name",
        "description",
    ]
    list_filter: ClassVar[list[str]] = [
        "layer",
    ]



@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    """Layer admin."""

    save_as = True
    list_display: ClassVar[list[str]] = ["name", "slug"]


@admin.register(ExternalLayer)
class ExternalLayerAdmin(admin.ModelAdmin):
    """Layer admin."""

    save_as = True
    list_display: ClassVar[list[str]] = ["name"]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Group admin."""

    save_as = True
    list_display: ClassVar[list[str]] = ["name"]


@admin.register(UserLocationType)
class UserLocationTypeAdmin(admin.ModelAdmin):
    """User Location Type admin."""

    save_as = True
    list_display: ClassVar[list[str]] = ["name"]


@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    """User Location admin."""

    save_as = True
    list_display: ClassVar[list[str]] = ["name", "type", "user", "camp"]
    list_filter: ClassVar[list[str]] = ["camp", "user"]
