from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin

from .models import ExternalLayer
from .models import Feature
from .models import Group
from .models import Layer


@admin.register(Feature)
class FeatureAdmin(LeafletGeoAdmin, admin.ModelAdmin):
    display_raw = True
    save_as = True
    list_display = [
        "name",
        "description",
    ]
    list_filter = [
        "layer",
    ]

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request)


@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ["name", "slug"]


@admin.register(ExternalLayer)
class ExternalLayerAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ["name"]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ["name"]
