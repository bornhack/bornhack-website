from __future__ import annotations

from django.views.generic import ListView

from camps.models import Camp


class PeopleView(ListView):
    template_name = "people.html"
    model = Camp
