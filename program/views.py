from collections import OrderedDict
import datetime
from django.views.generic import ListView, TemplateView, DetailView
from camps.mixins import CampViewMixin
from . import models
from django.http import Http404
import datetime
from django.conf import settings


class SpeakerDetailView(CampViewMixin, DetailView):
    model = models.Speaker
    template_name = 'speaker_detail.html'


class SpeakerListView(CampViewMixin, ListView):
    model = models.Speaker
    template_name = 'speaker_list.html'

    def get_queryset(self, *args, **kwargs):
        return models.Speaker.objects.filter(camp=self.camp)


class EventListView(CampViewMixin, ListView):
    model = models.Event
    template_name = 'event_list.html'


class ProgramOverviewView(CampViewMixin, ListView):
    model = models.Event
    template_name = 'program_overview.html'

    def dispatch(self, *args, **kwargs):
        """ If an event type has been supplied check if it is valid """
        if 'type' in self.request.GET:
            try:
                eventtype = models.EventType.objects.get(
                    slug=self.request.GET['type']
                )
            except models.EventType.DoesNotExist:
                raise Http404
        return super(ProgramOverviewView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProgramOverviewView, self).get_context_data(**kwargs)
        if 'type' in self.request.GET:
            context['eventtype'] = models.EventType.objects.get(slug=self.request.GET['type'])
        return context


class ProgramDayView(CampViewMixin, TemplateView):
    template_name = 'program_day.html'
    def dispatch(self, *args, **kwargs):
        """ If an event type has been supplied check if it is valid """
        if 'type' in self.request.GET:
            try:
                eventtype = models.EventType.objects.get(
                    slug=self.request.GET['type']
                )
            except models.EventType.DoesNotExist:
                raise Http404
        return super(ProgramDayView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProgramDayView, self).get_context_data(**kwargs)
        when = datetime.datetime(year=int(self.kwargs['year']), month=int(self.kwargs['month']), day=int(self.kwargs['day']))
        eventinstances = models.EventInstance.objects.filter(event__in=self.camp.events.all())
        skip = []
        for ei in eventinstances:
            if ei.schedule_date != when.date():
                skip.append(ei.id)
            else:
                if 'type' in self.request.GET:
                    eventtype = models.EventType.objects.get(
                        slug=self.request.GET['type']
                    )
                    if ei.event.event_type != eventtype:
                        skip.append(ei.id)
        context['eventinstances'] = eventinstances.exclude(id__in=skip).order_by('event__event_type')

        start = when + datetime.timedelta(hours=settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS)
        timeslots = []
        # calculate how many timeslots we have in the schedule based on the lenght of the timeslots in minutes,
        # and the number of minutes in 24 hours
        for i in range(0,(24*60)/settings.SCHEDULE_TIMESLOT_LENGTH_MINUTES):
            timeslot = start + datetime.timedelta(minutes=i*settings.SCHEDULE_TIMESLOT_LENGTH_MINUTES)
            timeslots.append(timeslot)
        context['timeslots'] = timeslots

        # include the components to make the urls
        context['urlyear'] = self.kwargs['year']
        context['urlmonth'] = self.kwargs['month']
        context['urlday'] = self.kwargs['day']

        if 'type' in self.request.GET:
            context['eventtype'] = models.EventType.objects.get(slug=self.request.GET['type'])

        return context



class EventDetailView(CampViewMixin, DetailView):
    model = models.Event
    template_name = 'program_event_detail.html'


class CallForSpeakersView(CampViewMixin, TemplateView):
    def get_template_names(self):
        return 'call_for_speakers_%s.html' % self.camp.slug


