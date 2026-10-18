from __future__ import annotations

import logging

from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView
from django.views.generic import ListView

from program.models import EventType

from .models import Camp
from .utils import get_closest_camp

logger = logging.getLogger(f"bornhack.{__name__}")


class CampRedirectView(View):
    def dispatch(self, request, *args, **kwargs):
        """Find closest camp and redirect to it."""
        camp = get_closest_camp(timezone.now(), max_days_from_prev=60)
        return redirect(kwargs["page"], camp_slug=camp.slug)


class CampDetailView(DetailView):
    model = Camp
    slug_url_kwarg = "camp_slug"

    def get_template_names(self) -> str:
        return f"{self.get_object().slug}_camp_detail.html"


class CampListView(ListView):
    model = Camp
    template_name = "camp_list.html"
    queryset = Camp.objects.all().order_by("camp")

    def get_context_data(self, **kwargs) -> dict[str, str]:
        """Add closest camp to context."""
        context = super().get_context_data(**kwargs)
        context["camp"] = get_closest_camp(timezone.now(), max_days_from_prev=60)
        return context


class CampStatsView(ListView):
    model = Camp
    template_name = "camp_stats.html"

    def get_queryset(self, **kwargs):
        return (
            Camp.objects.prefetch_related("teams")
            .annotate_participants(checked_in=True)
            .annotate_participants(checked_in=False)
            .annotate_volunteer_count()
            .filter(camp__startswith__lt=timezone.now())
            .order_by("-camp")
        )

    def get_context_data(self, **kwargs) -> dict[str, str]:
        """Add closest camp to context."""
        context = super().get_context_data(**kwargs)
        context["closest_camp"] = get_closest_camp(timezone.now(), max_days_from_prev=60)
        context["event_types"] = EventType.objects.order_by("name").all()
        return context
