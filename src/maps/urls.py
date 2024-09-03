from django.urls import re_path
from django.urls import path
from django.urls import include

from .views import MapProxyView
from .views import MapView
from .views import MapMarkerView
from .views import LayerGeoJSONView

app_name = "maps"

urlpatterns = [
    path("map/", MapView.as_view(), name="map"),
    path("marker/<color>/", MapMarkerView.as_view(), name="marker"),
    path("<slug:layer_slug>/", include([
        path("geojson/", LayerGeoJSONView.as_view(), name="map_layer_geojson"),
    ])),
    re_path("kfproxy/(?P<path>.*)", MapProxyView.as_view(), name="proxy"),
]
