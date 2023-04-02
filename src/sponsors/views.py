from django.db.models import Sum
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


class AllSponsorsView(ListView):
    model = Sponsor
    template_name = "allsponsors.html"
    context_object_name = "sponsors"

    def get_queryset(self, **kwargs):
        sponsors = (
            Sponsor.objects.order_by("name", "tier__camp__buildup")
            .distinct("name")
            .values()
        )
        for s in sponsors:
            years = Sponsor.objects.filter(name=s["name"])
            # score is 10 for each year minus tier weight, aggregated across all years
            s["score"] = years.annotate(score=10 - Sum("tier__weight")).aggregate(
                Sum("score"),
            )["score__sum"]
            s["years"] = [
                x["tier__camp__buildup"].lower.year
                for x in years.values("tier__camp__buildup")
            ]
        return sorted(sponsors, key=lambda item: item["score"], reverse=True)
