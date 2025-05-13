"""URL config for the wishlist app."""

from __future__ import annotations

from django.urls import path

from .views import WishDetailView
from .views import WishListView

app_name = "wishlist"
urlpatterns = [
    path("", WishListView.as_view(), name="list"),
    path("<slug:wish_slug>/", WishDetailView.as_view(), name="detail"),
]
