"""Maps URLS File."""

from __future__ import annotations

from django.urls import include
from django.urls import path
from django.urls import re_path

from .views import LayerGeoJSONView
from .views import LayerJsonView
from .views import MapMarkerView
from .views import MapProxyView

app_name = "maps"

urlpatterns = [
    path("marker/<color>/", MapMarkerView.as_view(), name="marker"),
    path("layers/", LayerJsonView.as_view(), name="map_layers_json"),
    path(
        "<slug:layer_slug>/",
        include(
            [
                path("geojson/", LayerGeoJSONView.as_view(), name="map_layer_geojson"),
            ],
        ),
    ),
    re_path("kfproxy/(?P<path>.*)", MapProxyView.as_view(), name="proxy"),
]
