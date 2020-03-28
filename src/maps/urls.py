from django.urls import re_path

from .views import MapProxyView

app_name = "maps"

urlpatterns = [
    re_path("kfproxy/(?P<path>.*)", MapProxyView.as_view(), name="proxy"),
]
