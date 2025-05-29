"""All URLs for the Token application."""

from __future__ import annotations

from django.urls import path
from django.urls import re_path

from .views import TokenDashboardListView
from .views import TokenSubmitFormView

app_name = "tokens"

urlpatterns = [
    path("", TokenDashboardListView.as_view(), name="dashboard"),
    re_path(
        r"(?P<token>[0-9a-zA-Z\.@]{12,32})/$",
        TokenSubmitFormView.as_view(),
        name="details",
    ),
    path("submit", TokenSubmitFormView.as_view(), name="submit"),
]
