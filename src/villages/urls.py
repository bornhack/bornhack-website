"""URLs for villages."""

from __future__ import annotations

from django.urls import include
from django.urls import path

from .views import VillageCreateView
from .views import VillageDeleteView
from .views import VillageDetailView
from .views import VillageListGeoJSONView
from .views import VillageListView
from .views import VillageMapView
from .views import VillageUpdateView

app_name = "villages"

urlpatterns = [
    path("", VillageListView.as_view(), name="village_list"),
    path("create/", VillageCreateView.as_view(), name="village_create"),
    path("geojson/", VillageListGeoJSONView.as_view(), name="villages_geojson"),
    path("map/", VillageMapView.as_view(), name="village_map"),
    path(
        "<slug:slug>/",
        include(
            [
                path("", VillageDetailView.as_view(), name="village_detail"),
                path("update/", VillageUpdateView.as_view(), name="village_update"),
                path("delete/", VillageDeleteView.as_view(), name="village_delete"),
            ]
        ),
    ),
]
