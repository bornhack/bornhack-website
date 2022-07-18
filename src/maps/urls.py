from django.urls import re_path, path

from .views import MapProxyView, GeometryCreateView

app_name = "maps"

urlpatterns = [
    re_path("kfproxy/(?P<path>.*)", MapProxyView.as_view(), name="proxy"),
    path("geometries/create/", GeometryCreateView.as_view(), name="geometry_create"),
]
