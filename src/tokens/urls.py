"""All URLs for the Token application."""
from __future__ import annotations

from django.urls import path
from django.urls import re_path

from .views import TokenFindListView
from .views import TokenFindView

app_name = "tokens"

urlpatterns = [
    path("", TokenFindListView.as_view(), name="tokenfind_list"),
    re_path(
        r"(?P<token>[0-9a-zA-Z\.@]{12,32})/$",
        TokenFindView.as_view(),
        name="details",
    ),
]
