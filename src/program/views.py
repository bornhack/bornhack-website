from collections import OrderedDict
import datetime
from django.views.generic import ListView, TemplateView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from camps.mixins import CampViewMixin
from . import models
from django.http import Http404
import datetime, os
from django.conf import settings
from django.views import View
from django.views.decorators.http import require_safe
from django.http import Http404
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class SpeakerCreateView(LoginRequiredMixin, CampViewMixin, CreateView):
    model = models.Speaker
    fields = ['name', 'biography', 'picture_small', 'picture_large']
    template_name = 'speaker_form.html'

    def get(self, request, *args, **kwargs):
        # first make sure we don't already have a speaker for this user for this camp
        try:
            speaker = models.Speaker.objects.get(user=request.user, camp=self.camp)
        except models.Speaker.DoesNotExist:
            # no speaker exists, just show the create speaker form
            return super(SpeakerCreateView, self).get(request, *args, **kwargs)

        # speaker already exists, where do we want to redirect?
        if speaker.submission_status == models.Speaker.SUBMISSION_DRAFT:
            messages.info(request, "You already have a draft speaker profile for %s, you can modify and submit it here" % self.camp.title)
            return redirect('speaker_edit', camp_slug=self.camp.slug, slug=speaker.slug)
        elif speaker.submission_status == models.Speaker.SUBMISSION_PENDING:
            messages.info(request, "You already have a pending speaker profile for %s, you can modify and resubmit it here" % self.camp.title)
            return redirect('speaker_edit', camp_slug=self.camp.slug, slug=speaker.slug)
        elif speaker.submission_status == models.Speaker.SUBMISSION_REJECTED:
            messages.info(request, "You already have a rejected speaker profile for %s, you can modify and resubmit it here" % self.camp.title)
            return redirect('speaker_edit', camp_slug=self.camp.slug, slug=speaker.slug)
        elif speaker.submission_status == models.Speaker.SUBMISSION_APPROVED:
            messages.info(request, "You already have an accepted speaker profile for %s, please contact the organisers if you want to modify it." % self.camp.title)
            return redirect('speaker_detail', camp_slug=self.camp.slug, slug=speaker.slug)
        else:
            # unknown submission status!
            return

    def form_valid(self, form):
        # set camp before saving
        form.instance.camp = self.camp
        form.instance.user = self.request.user
        speaker = form.save()
        return redirect(reverse('speaker_detail', kwargs={'camp_slug': speaker.camp.slug, 'slug': speaker.slug}))


class SpeakerEditView(LoginRequiredMixin, CampViewMixin, UpdateView):
    model = models.Speaker
    fields = ['name', 'biography', 'picture_small', 'picture_large']
    template_name = 'speaker_form.html'

    def dispatch(self, request, *args, **kwargs):
        # call super dispatch now because it ets self.camp which is needed below
        response = super(SpeakerEditView, self).dispatch(request, *args, **kwargs)

        # first make sure that this speaker belongs to the logged in user
        if self.get_object().user.username != request.user.username:
            messages.error(request, "No thanks")
            return redirect(reverse('speaker_detail', kwargs={'camp_slug': self.get_object().camp.slug, 'slug': self.get_object().slug}))

        if self.get_object().submission_status == models.Speaker.SUBMISSION_PENDING:
            messages.info(request, "Your speaker profile for %s has already been submitted. If you modify it you will have to resubmit it." % self.get_object().camp.title)
        elif self.get_object().submission_status == models.Speaker.SUBMISSION_REJECTED:
            messages.info(request, "When you are done editing you will have to resubmit your speaker profile." % self.get_object().camp.title)
        elif self.get_object().submission_status == models.Speaker.SUBMISSION_APPROVED:
            messages.error(request, "Your speaker profile for %s has already been approved. Please contact the organisers if you want to modify it." % self.get_object().camp.title)
            return redirect(reverse('speaker_detail', kwargs={'camp_slug': self.get_object().camp.slug, 'slug': self.get_object().slug}))

        # alright, render the form
        return super(SpeakerEditView, self).dispatch(request, *args, **kwargs)


@method_decorator(require_safe, name='dispatch')
class SpeakerPictureView(CampViewMixin, DetailView):
    model = models.Speaker

    def get(self, request, *args, **kwargs):
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

    def get_queryset(self, *args, **kwargs):
        return models.Speaker.objects.filter(
            camp=self.camp,
            submission_status=models.Speaker.SUBMISSION_APPROVED
        )


class EventListView(CampViewMixin, ListView):
    model = models.Event
    template_name = 'event_list.html'


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


class EventDetailView(CampViewMixin, DetailView):
    model = models.Event
    template_name = 'schedule_event_detail.html'


class CallForSpeakersView(CampViewMixin, TemplateView):
    def get_template_names(self):
        return '%s_call_for_speakers.html' % self.camp.slug

