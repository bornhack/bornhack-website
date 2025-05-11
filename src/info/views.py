from __future__ import annotations

from django.views.generic import ListView

from camps.mixins import CampViewMixin

from .models import InfoCategory


class CampInfoView(CampViewMixin, ListView):
    model = InfoCategory
    template_name = "info.html"
    context_object_name = "categories"

    def get_queryset(self):
        queryset = super().get_queryset()
        # do not show categories with 0 items
        return queryset.exclude(infoitems__isnull=True)
