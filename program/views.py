from collections import OrderedDict

import datetime
from django.views.generic import ListView, TemplateView, DetailView
from camps.mixins import CampViewMixin

from . import models


class SpeakerDetailView(CampViewMixin, DetailView):
    model = models.Speaker
    template_name = 'speaker_detail.html'


class SpeakerListView(CampViewMixin, ListView):
    model = models.Speaker
    template_name = 'speaker_list.html'


class EventListView(CampViewMixin, ListView):
    model = models.Event
    template_name = 'event_list.html'


class ProgramOverviewView(CampViewMixin, ListView):
    model = models.Event
    template_name = 'program_overview.html'


class ProgramDayView(CampViewMixin, TemplateView):
    template_name = 'program_day.html'


class EventDetailView(CampViewMixin, DetailView):
    model = models.Event
    template_name = 'program_event_detail.html'


