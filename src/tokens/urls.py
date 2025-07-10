"""All URLs for the Token application."""

from __future__ import annotations

from django.urls import path

from .views import TokenDashboardListView
from .views import TokenSubmitFormView

app_name = "tokens"

urlpatterns = [
    path("", TokenDashboardListView.as_view(), name="dashboard"),
    path("<str:token>", TokenSubmitFormView.as_view()),  # Allow token in URL
    path("submit", TokenSubmitFormView.as_view(), name="submit"),
]
