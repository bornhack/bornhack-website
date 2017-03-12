from django.views.generic import ListView, TemplateView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.conf import settings
from django.views.decorators.http import require_safe
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from camps.mixins import CampViewMixin
from .mixins import CreateProposalMixin, EnsureUnpprovedProposalMixin, EnsureUserOwnsProposalMixin, EnsureWritableCampMixin
from . import models
import datetime, os


############## proposals ########################################################


class ProposalListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = models.SpeakerProposal
    template_name = 'proposal_list.html'
    context_object_name = 'speakerproposal_list'

    def get_queryset(self, **kwargs):
        # only show speaker proposals for the current user
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add eventproposals to the context
        context['eventproposal_list'] = models.EventProposal.objects.filter(camp=self.camp, user=self.request.user)
        return context


class SpeakerProposalCreateView(LoginRequiredMixin, CampViewMixin, CreateProposalMixin, EnsureWritableCampMixin, CreateView):
    model = models.SpeakerProposal
    fields = ['name', 'biography', 'picture_small', 'picture_large']
    template_name = 'speakerproposal_form.html'


class SpeakerProposalUpdateView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, EnsureUnpprovedProposalMixin, EnsureWritableCampMixin, UpdateView):
    model = models.SpeakerProposal
    fields = ['name', 'biography', 'picture_small', 'picture_large']
    template_name = 'speakerproposal_form.html'

    def get_success_url(self):
        return reverse('proposal_list', kwargs={'camp_slug': self.camp.slug})


class SpeakerProposalDetailView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, DetailView):
    model = models.SpeakerProposal
    template_name = 'speakerproposal_detail.html'


@method_decorator(require_safe, name='dispatch')
class SpeakerProposalPictureView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, DetailView):
    model = models.SpeakerProposal

    def get(self, request, *args, **kwargs):
        # is the speaker public, or owned by current user?
        if not self.get_object().user != request.user:
            raise Http404()

        # do we have the requested picture?
        if kwargs['picture'] == 'thumbnail':
            if self.get_object().picture_small:
                picture = self.get_object().picture_small
            else:
                raise Http404()
        elif kwargs['picture'] == 'large':
            if self.get_object().picture_large:
                picture = self.get_object().picture_large
            else:
                raise Http404()
        else:
            raise Http404()

        # make nginx return the picture using X-Accel-Redirect
        # (this works for nginx only, other webservers use x-sendfile),
        # TODO: what about runserver mode here?
        response = HttpResponse()
        response['X-Accel-Redirect'] = '/public/speakerproposals/%(campslug)s/%(proposaluuid)s/%(filename)s' % {
            'campslug': self.camp.slug,
            'proposaluuid': self.get_object().uuid,
            'filename': os.path.basename(picture.name),
        }
        response['Content-Type'] = ''
        return response


class EventProposalCreateView(LoginRequiredMixin, CampViewMixin, CreateProposalMixin, EnsureWritableCampMixin, CreateView):
    model = models.EventProposal
    fields = ['title', 'abstract', 'event_type', 'speakers']
    template_name = 'eventproposal_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['speakers'].queryset = models.SpeakerProposal.objects.filter(camp=self.camp, user=self.request.user)
        context['form'].fields['event_type'].queryset = models.EventType.objects.filter(public=True)
        return context


class EventProposalUpdateView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, EnsureUnpprovedProposalMixin, EnsureWritableCampMixin, UpdateView):
    model = models.EventProposal
    fields = ['title', 'abstract', 'event_type', 'speakers']
    template_name = 'eventproposal_form.html'

    def get_success_url(self):
        return reverse('proposal_list', kwargs={'camp_slug': self.camp.slug})


class EventProposalDetailView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, DetailView):
    model = models.EventProposal
    template_name = 'eventproposal_detail.html'


################## speakers ###############################################


@method_decorator(require_safe, name='dispatch')
class SpeakerPictureView(CampViewMixin, DetailView):
    model = models.Speaker

    def get(self, request, *args, **kwargs):
        # is the speaker public, or owned by current user?
        if not self.get_object().is_public and self.get_object().user != request.user:
            raise Http404()

        # do we have the requested picture?
        if kwargs['picture'] == 'thumbnail':
            if self.get_object().picture_small:
                picture = self.get_object().picture_small
            else:
                raise Http404()
        elif kwargs['picture'] == 'large':
            if self.get_object().picture_large:
                picture = self.get_object().picture_large
            else:
                raise Http404()
        else:
            raise Http404()

        # make nginx return the picture using X-Accel-Redirect
        # (this works for nginx only, other webservers use x-sendfile),
        # TODO: what about runserver mode here?
        response = HttpResponse()
        response['X-Accel-Redirect'] = '/public/speakers/%(campslug)s/%(speakerslug)s/%(filename)s' % {
            'campslug': self.camp.slug,
            'speakerslug': self.get_object().slug,
            'filename': os.path.basename(picture.name),
        }
        response['Content-Type'] = ''
        return response


class SpeakerDetailView(CampViewMixin, DetailView):
    model = models.Speaker
    template_name = 'speaker_detail.html'


class SpeakerListView(CampViewMixin, ListView):
    model = models.Speaker
    template_name = 'speaker_list.html'


################## events ##############################################


class EventListView(CampViewMixin, ListView):
    model = models.Event
    template_name = 'event_list.html'


class EventDetailView(CampViewMixin, DetailView):
    model = models.Event
    template_name = 'schedule_event_detail.html'


################## schedule #############################################


class ScheduleView(CampViewMixin, TemplateView):
    def get_template_names(self):
        if 'day' in self.kwargs:
            return 'schedule_day.html'
        return 'schedule_overview.html'

    def get_context_data(self, *args, **kwargs):
        if 'type' in self.request.GET:
            try:
                eventtype = models.EventType.objects.get(
                    slug=self.request.GET['type']
                )
            except models.EventType.DoesNotExist:
                raise Http404

        if 'location' in self.request.GET:
            try:
                eventlocation = models.EventLocation.objects.get(
                    slug=self.request.GET['location'],
                    camp=self.camp,
                )
            except models.EventLocation.DoesNotExist:
                raise Http404

        context = super(ScheduleView, self).get_context_data(**kwargs)
        eventinstances = models.EventInstance.objects.filter(event__in=self.camp.events.all())

        if 'type' in self.request.GET:
            context['eventtype'] = eventtype
            eventinstances = eventinstances.filter(event__event_type=eventtype)

        if 'location' in self.request.GET:
            context['location'] = eventlocation
            eventinstances = eventinstances.filter(location=eventlocation)
        context['eventinstances'] = eventinstances

        # Do stuff if we are dealing with a day schedule
        if 'day' in kwargs:
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
            eventinstances = eventinstances.exclude(id__in=skip).order_by('event__event_type')
            if 'location' in self.request.GET:
                eventlocation = models.EventLocation.objects.get(
                    camp=self.camp,
                    slug=self.request.GET['location']
                )
                eventinstances = eventinstances.filter(location=eventlocation)

            context['eventinstances'] = eventinstances

            start = when + datetime.timedelta(hours=settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS)
            timeslots = []
            # calculate how many timeslots we have in the schedule based on the lenght of the timeslots in minutes,
            # and the number of minutes in 24 hours
            for i in range(0,int((24*60)/settings.SCHEDULE_TIMESLOT_LENGTH_MINUTES)):
                timeslot = start + datetime.timedelta(minutes=i*settings.SCHEDULE_TIMESLOT_LENGTH_MINUTES)
                timeslots.append(timeslot)
            context['timeslots'] = timeslots

            # include the components to make the urls
            context['urlyear'] = self.kwargs['year']
            context['urlmonth'] = self.kwargs['month']
            context['urlday'] = self.kwargs['day']

        return context


class CallForSpeakersView(CampViewMixin, TemplateView):
    def get_template_names(self):
        return '%s_call_for_speakers.html' % self.camp.slug

