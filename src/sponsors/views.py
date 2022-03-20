from django.views.generic import ListView

from .models import Sponsor
from camps.mixins import CampViewMixin


class SponsorsView(CampViewMixin, ListView):
    model = Sponsor
    template_name = "sponsors.html"
    context_object_name = "sponsors"

    def get_queryset(self, **kwargs):
        queryset = super().get_queryset()
        return queryset.filter(tier__camp=self.camp).order_by("tier__weight", "name")
