from __future__ import annotations

from django.db.models import DateTimeField
from django.db.models import F
from django.db.models import Sum
from django.db.models.functions import ExtractYear
from django.db.models.functions import Lower
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic import TemplateView

from camps.mixins import CampViewMixin

from .models import Sponsor


class CallForSponsorsView(CampViewMixin, TemplateView):
    template_name = "call_for_sponsors.html"


class SponsorsView(CampViewMixin, ListView):
    model = Sponsor
    template_name = "sponsors.html"
    context_object_name = "sponsors"

    def get_queryset(self, **kwargs):
        queryset = super().get_queryset()
        return queryset.filter(tier__camp=self.camp).order_by("tier__weight", "name")

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if self.object_list.count() < 1:
            url = reverse("call_for_sponsors", kwargs={"camp_slug": self.camp.slug})
            return redirect(url)
        return super().get(request, *args, **kwargs)


class AllSponsorsView(ListView):
    model = Sponsor
    template_name = "allsponsors.html"
    context_object_name = "sponsors"

    def get_queryset(self, **kwargs):
        sponsors = Sponsor.objects.order_by("name", "tier__camp__buildup").distinct("name").values()

        this_year = timezone.now().year

        for s in sponsors:
            years = Sponsor.objects.filter(name=s["name"])
            # sponsor score is 100 for each year, minus sponsor tier weight*20, minus 1 per year
            # passed since the sponsorship, aggregated across all sponsorship years
            s["score"] = years.annotate(
                # Get the year of the camp
                camp_start=Lower(
                    F("tier__camp__camp"),
                    output_field=DateTimeField(),
                ),
                # Calculate the difference between the year of the camp and this year, this is to
                # make sure that more recent sponsors are ranked higher than older sponsors
                year_score=this_year - ExtractYear("camp_start"),
                # Calculate the score for this sponsor
                score=100 - (Sum("tier__weight") * 20) - F("year_score"),
            ).aggregate(Sum("score"))["score__sum"]
            # years is a list of all the years this sponsor has been a sponsor
            s["years"] = sorted(
                [x["tier__camp__buildup"].lower.year for x in years.values("tier__camp__buildup")],
            )
        return sorted(sponsors, key=lambda item: item["score"], reverse=True)
