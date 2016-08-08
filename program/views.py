from collections import OrderedDict

import datetime
from django.views.generic import ListView, TemplateView, DetailView

from camps.models import Day
from . import models


class SpeakerDetailView(DetailView):
    model = models.Speaker
    template_name = 'speaker_detail.html'

class SpeakerListView(ListView):
    model = models.Speaker
    template_name = 'speaker_list.html'

class EventListView(ListView):
    model = models.Event
    template_name = 'event_list.html'

class ProgramOverviewView(ListView):
    model = models.Event
    template_name = 'program_overview.html'

    def get_context_data(self, **kwargs):
        context = super(
            ProgramOverviewView, self
        ).get_context_data(**kwargs)

        days = Day.objects.all()
        context['days'] = days

        filter = {}
        if 'type' in self.request.GET:
            event_type = self.request.GET['type']
            filter["event_type__slug"] = event_type

        context['day_events'] = OrderedDict([
            (
                day,
                self.get_queryset().filter(
                    days__in=[day],
                    **filter
                ).order_by(
                    'start'
                )
            )
            for day in days
        ])

        context['event_types'] = models.EventType.objects.all()

        return context


class ProgramDayView(TemplateView):
    template_name = 'program_day.html'

    def get_context_data(self, **kwargs):
        context = super(ProgramDayView, self).get_context_data(**kwargs)
        year = int(kwargs['year'])
        month = int(kwargs['month'])
        day = int(kwargs['day'])
        date = datetime.date(year=year, month=month, day=day)
        day = Day.objects.filter(date=date)
        context['date'] = date
        context['events'] = models.Event.objects.filter(days=day).order_by('start', 'event_type')
        context['event_types'] = models.EventType.objects.all()
        context['days'] = Day.objects.filter(date__year=year)
        return context


class EventDetailView(DetailView):
    model = models.Event
    template_name = 'program_event_detail.html'

    def get_context_data(self, **kwargs):
        context = super(EventDetailView, self).get_context_data(**kwargs)
        # TODO: date__year is hardcoded here - need fix for 2017 :P
        context['days'] = Day.objects.filter(date__year=2016)
        return context
