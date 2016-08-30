from collections import OrderedDict

import datetime
from django.views.generic import ListView, TemplateView, DetailView
from django.views import View
from django.http.response import HttpResponse

from camps.models import Day
from . import models

import icalendar
from icalendar import vDatetime

def gen_icalevents(event):
    for i in event.days.all():
        ievent = icalendar.Event()
        ievent['summary'] = event.title

        newdate = datetime.datetime.combine(i.date, datetime.time(event.start.hour, event.start.minute, event.start.second))
        ievent['dtstart'] = vDatetime(newdate).to_ical()

        newdate = datetime.datetime.combine(i.date, datetime.time(event.end.hour, event.end.minute, event.end.second))
        ievent['dtend'] = vDatetime(newdate).to_ical()

        yield ievent

def gen_ics(events):
    cal = icalendar.Calendar()
    for event in events:
        for ical_event in gen_icalevents(event):
            cal.add_component(ical_event)
    return cal.to_ical()

class ICSView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(gen_ics(models.Event.objects.all()))

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
        context['events'] = models.Event.objects.filter(days=day).order_by('event_type', 'start')
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
