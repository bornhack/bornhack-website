from django.urls import re_path
from django.urls import path

from .views import MapProxyView
from .views import MapView

app_name = "maps"

urlpatterns = [
    path("map/", MapView.as_view(), name="map"),
    re_path("kfproxy/(?P<path>.*)", MapProxyView.as_view(), name="proxy"),
]
