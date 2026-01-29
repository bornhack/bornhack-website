from __future__ import annotations

from django.views.generic import ListView
from django.db.models import Prefetch

from camps.models import Camp
from teams.models import TeamMember


class PeopleView(ListView):
    template_name = "people.html"
    model = Camp

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            "teams",
            Prefetch(
                "teams__teammember_set",
                queryset=TeamMember.objects.select_related("user__profile")
            )
        )

