import datetime
import logging
import os

from django.views.generic import ListView, TemplateView, DetailView, View
from django.views.generic.edit import CreateView, UpdateView
from django.conf import settings
from django.views.decorators.http import require_safe
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q

import icalendar

from camps.mixins import CampViewMixin
from .mixins import (
    CreateProposalMixin,
    EnsureUnapprovedProposalMixin,
    EnsureUserOwnsProposalMixin,
    EnsureWritableCampMixin,
    PictureViewMixin,
    EnsureCFSOpenMixin
)
from .email import (
    add_speakerproposal_updated_email,
    add_eventproposal_updated_email
)
from . import models
logger = logging.getLogger("bornhack.%s" % __name__)


############## ical calendar ########################################################


class ICSView(CampViewMixin, View):
    def get(self, request, *args, **kwargs):
        eventinstances = models.EventInstance.objects.filter(event__camp=self.camp)

        # Type query
        type_query = request.GET.get('type', None)
        if type_query:
            type_slugs = type_query.split(',')
            types = models.EventType.objects.filter(
                slug__in=type_slugs
            )
            eventinstances = eventinstances.filter(event__event_type__in=types)

        # Location query
        location_query = request.GET.get('location', None)
        if location_query:
            location_slugs = location_query.split(',')
            locations = models.EventLocation.objects.filter(
                slug__in=location_slugs,
                camp=self.camp,
            )
            eventinstances = eventinstances.filter(location__in=locations)

        # Video recording query
        video_query = request.GET.get('video', None)
        if video_query:
            video_states = video_query.split(',')
            query_kwargs = {}

            if 'has-recording' in video_states:
                query_kwargs['event__video_url__isnull'] = False

            if 'to-be-recorded' in video_states:
                query_kwargs['event__video_recording'] = True

            if 'not-to-be-recorded' in video_states:
                if 'event__video_recording' in query_kwargs:
                    del query_kwargs['event__video_recording']
                else:
                    query_kwargs['event__video_recording'] = False

            eventinstances = eventinstances.filter(**query_kwargs)

        cal = icalendar.Calendar()
        for event_instance in eventinstances:
            cal.add_component(event_instance.get_ics_event())

        response = HttpResponse(cal.to_ical())
        response['Content-Type'] = 'text/calendar'
        response['Content-Disposition'] = 'inline; filename={}.ics'.format(self.camp.slug)
        return response


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
        # also add eventproposals to the context
        context['eventproposal_list'] = models.EventProposal.objects.filter(camp=self.camp, user=self.request.user)
        return context


class SpeakerProposalCreateView(LoginRequiredMixin, CampViewMixin, CreateProposalMixin, EnsureWritableCampMixin, EnsureCFSOpenMixin, CreateView):
    model = models.SpeakerProposal
    fields = ['name', 'biography', 'picture_small', 'picture_large', 'submission_notes']
    template_name = 'speakerproposal_form.html'

    def get_success_url(self):
        return reverse('proposal_list', kwargs={'camp_slug': self.camp.slug})


class SpeakerProposalUpdateView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, EnsureWritableCampMixin, EnsureCFSOpenMixin, UpdateView):
    model = models.SpeakerProposal
    fields = ['name', 'biography', 'picture_small', 'picture_large', 'submission_notes']
    template_name = 'speakerproposal_form.html'

    def get_success_url(self):
        return reverse('proposal_list', kwargs={'camp_slug': self.camp.slug})

    def form_valid(self, form):
        if form.instance.proposal_status == models.UserSubmittedModel.PROPOSAL_PENDING:
            messages.warning(self.request, "Your speaker proposal has been reverted to status draft. Please submit it again when you are ready.")
            form.instance.proposal_status = models.UserSubmittedModel.PROPOSAL_DRAFT

        if form.instance.proposal_status == models.UserSubmittedModel.PROPOSAL_APPROVED:
            messages.warning(self.request, "Your speaker proposal has been set to modified after approval. Please await approval of the changes.")
            form.instance.proposal_status = models.UserSubmittedModel.PROPOSAL_MODIFIED_AFTER_APPROVAL
            if not add_speakerproposal_updated_email(form.instance):
                logger.error(
                    'Unable to add update email to queue for speaker: {}'.format(form.instance)
                )

        return super().form_valid(form)


class SpeakerProposalSubmitView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, EnsureUnapprovedProposalMixin, EnsureWritableCampMixin, EnsureCFSOpenMixin, UpdateView):
    model = models.SpeakerProposal
    fields = []
    template_name = 'speakerproposal_submit.html'

    def get_success_url(self):
        return reverse('proposal_list', kwargs={'camp_slug': self.camp.slug})

    def form_valid(self, form):
        form.instance.proposal_status = models.UserSubmittedModel.PROPOSAL_PENDING
        messages.info(self.request, "Your proposal has been submitted and is now pending approval")
        return super().form_valid(form)


class SpeakerProposalDetailView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, DetailView):
    model = models.SpeakerProposal
    template_name = 'speakerproposal_detail.html'


@method_decorator(require_safe, name='dispatch')
class SpeakerProposalPictureView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, PictureViewMixin, DetailView):
    model = models.SpeakerProposal

    def get(self, request, *args, **kwargs):
        # is the proposal owned by current user?
        if self.get_object().user != request.user:
            raise Http404()

        # get and return the response
        response = self.get_picture_response('/public/speakerproposals/%(campslug)s/%(proposaluuid)s/%(filename)s' % {
            'campslug': self.camp.slug,
            'proposaluuid': self.get_object().uuid,
            'filename': os.path.basename(self.picture.name),
        })

        return response


class EventProposalCreateView(LoginRequiredMixin, CampViewMixin, CreateProposalMixin, EnsureWritableCampMixin, EnsureCFSOpenMixin, CreateView):
    model = models.EventProposal
    fields = ['title', 'abstract', 'event_type', 'speakers', 'allow_video_recording', 'submission_notes']
    template_name = 'eventproposal_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['speakers'].queryset = models.SpeakerProposal.objects.filter(camp=self.camp, user=self.request.user)
        context['form'].fields['event_type'].queryset = models.EventType.objects.filter(public=True)
        return context


class EventProposalUpdateView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, EnsureWritableCampMixin, EnsureCFSOpenMixin, UpdateView):
    model = models.EventProposal
    fields = ['title', 'abstract', 'event_type', 'speakers', 'allow_video_recording', 'submission_notes']
    template_name = 'eventproposal_form.html'

    def get_success_url(self):
        return reverse('proposal_list', kwargs={'camp_slug': self.camp.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['speakers'].queryset = models.SpeakerProposal.objects.filter(camp=self.camp, user=self.request.user)
        context['form'].fields['event_type'].queryset = models.EventType.objects.filter(public=True)
        return context

    def form_valid(self, form):
        if form.instance.proposal_status == models.UserSubmittedModel.PROPOSAL_PENDING:
            messages.warning(self.request, "Your event proposal has been reverted to status draft. Please submit it again when you are ready.")
            form.instance.proposal_status = models.UserSubmittedModel.PROPOSAL_DRAFT

        if form.instance.proposal_status == models.UserSubmittedModel.PROPOSAL_APPROVED:
            messages.warning(self.request, "Your event proposal has been set to status modified after approval. Please await approval of the changes.")
            form.instance.proposal_status = models.UserSubmittedModel.PROPOSAL_MODIFIED_AFTER_APPROVAL
            if not add_eventproposal_updated_email(form.instance):
                logger.error(
                    'Unable to add update email to queue for event: {}'.format(form.instance)
                )

        return super().form_valid(form)


class EventProposalSubmitView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, EnsureUnapprovedProposalMixin, EnsureWritableCampMixin, EnsureCFSOpenMixin, UpdateView):
    model = models.EventProposal
    fields = []
    template_name = 'eventproposal_submit.html'

    def get_success_url(self):
        return reverse('proposal_list', kwargs={'camp_slug': self.camp.slug})

    def form_valid(self, form):
        form.instance.proposal_status = models.UserSubmittedModel.PROPOSAL_PENDING
        messages.info(self.request, "Your proposal has been submitted and is now pending approval")
        return super().form_valid(form)


class EventProposalDetailView(LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, DetailView):
    model = models.EventProposal
    template_name = 'eventproposal_detail.html'


################## speakers ###############################################


@method_decorator(require_safe, name='dispatch')
class SpeakerPictureView(CampViewMixin, PictureViewMixin, DetailView):
    model = models.Speaker

    def get(self, request, *args, **kwargs):
        # get and return the response
        response = self.get_picture_response(path='/public/speakers/%(campslug)s/%(slug)s/%(filename)s' % {
            'campslug': self.camp.slug,
            'slug': self.get_object().slug,
            'filename': os.path.basename(self.picture.name),
        })
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


class NoScriptScheduleView(CampViewMixin, TemplateView):
    template_name = "noscript_schedule_view.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['eventinstances'] = models.EventInstance.objects.filter(event__camp=self.camp).order_by('when')
        return context



class ScheduleView(CampViewMixin, TemplateView):
    template_name = 'schedule_overview.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ScheduleView, self).get_context_data(**kwargs)
        context['schedule_midnight_offset_hours'] = settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS;
        return context


class CallForSpeakersView(CampViewMixin, TemplateView):
    def get_template_names(self):
        return '%s_call_for_speakers.html' % self.camp.slug

