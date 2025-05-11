"""Views related to wishlist functionality."""

from __future__ import annotations

from django.views.generic import DetailView
from django.views.generic import ListView

from .models import Wish


class WishListView(ListView[Wish]):
    """List wishes."""

    model = Wish
    template_name = "wish_list.html"

    def get_queryset(self, **kwargs):
        """Only show unfulfilled wishes."""
        return super().get_queryset().filter(fulfilled=False)


class WishDetailView(DetailView[Wish]):
    """Wish detailview."""

    model = Wish
    template_name = "wish_detail.html"
    slug_url_kwarg = "wish_slug"
