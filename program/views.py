from collections import OrderedDict

from django.views.generic import ListView

from camps.models import Day
from . import models


class ProgramView(ListView):
    model = models.Event
    template_name = 'program.html'

    def get_context_data(self, **kwargs):
        context = super(
            ProgramView, self
        ).get_context_data(**kwargs)

        days = Day.objects.all()

        context['days'] = OrderedDict([
            (day, self.get_queryset().filter(days__in=[day]))
            for day in days
        ])

        return context

