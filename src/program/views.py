import logging
import os
from collections import OrderedDict

from django.views.generic import ListView, TemplateView, DetailView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.conf import settings
from django.views.decorators.http import require_safe
from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.template import Engine, Context
from django.shortcuts import redirect
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from betterforms.multiform import MultiModelForm
import icalendar

from camps.mixins import CampViewMixin
from .mixins import (
    EnsureUnapprovedProposalMixin,
    EnsureUserOwnsProposalMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UrlViewMixin,
)
from .email import (
    add_speakerproposal_updated_email,
    add_eventproposal_updated_email
)
from . import models
from .utils import get_speakerproposal_form_class, get_eventproposal_form_class
from .forms import BaseSpeakerProposalForm


logger = logging.getLogger("bornhack.%s" % __name__)


###################################################################################################
# ical calendar


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


###################################################################################################
# proposals list view


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
        context['eventproposal_list'] = models.EventProposal.objects.filter(track__camp=self.camp, user=self.request.user)
        context['eventtype_list'] = models.EventType.objects.filter(public=True)
        return context


###################################################################################################
# speakerproposal views


class SpeakerProposalCreateView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureCFPOpenMixin, CreateView):
    """ This view allows a user to create a new SpeakerProposal linked to an existing EventProposal """
    model = models.SpeakerProposal
    template_name = 'speakerproposal_form.html'

    def dispatch(self, request, *args, **kwargs):
        """ Get the eventproposal object """
        self.eventproposal = get_object_or_404(models.EventProposal, pk=kwargs['event_uuid'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug})

    def get_form_class(self):
        return get_speakerproposal_form_class(eventtype=self.eventproposal.event_type)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['eventproposal'] = self.eventproposal
        return context

    def form_valid(self, form):
        # set user before saving
        form.instance.user = self.request.user
        form.instance.camp = self.camp
        speakerproposal = form.save()

        # add speakerproposal to eventproposal
        self.eventproposal.speakers.add(speakerproposal)

        return redirect(
            reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug})
        )


class SpeakerProposalUpdateView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureUserOwnsProposalMixin, EnsureCFPOpenMixin, UpdateView):
    """
    This view allows a user to update an existing SpeakerProposal.
    """
    model = models.SpeakerProposal
    template_name = 'speakerproposal_form.html'

    def get_success_url(self):
        return reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug})

    def get_form_class(self):
        """ Get the appropriate form class based on the eventtype """
        if self.get_object().eventproposals.count() == 1:
            # determine which form to use based on the type of event associated with the proposal
            return get_speakerproposal_form_class(self.get_object().eventproposals.get().event_type)
        else:
            # more than one eventproposal. If all events are the same type we can still show a non-generic form here
            eventtypes = set()
            for ep in self.get_object().eventproposals.all():
                eventtypes.add(ep.event_type)
            if len(eventtypes) == 1:
                return get_speakerproposal_form_class(ep.event_type)
            # more than one type of event for this person, return the generic speakerproposal form
            return BaseSpeakerProposalForm


class SpeakerProposalDeleteView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureUserOwnsProposalMixin, EnsureCFPOpenMixin, DeleteView):
    """
    This view allows a user to delete an existing SpeakerProposal object, as long as it is not linked to any EventProposals
    """
    model = models.SpeakerProposal
    template_name = 'proposal_delete.html'

    def get(self, request, *args, **kwargs):
        # do not permit deleting if this speakerproposal is linked to any eventproposals
        if self.get_object().eventproposals.exists():
            messages.error(request, "Cannot delete a person while it is associated with one or more eventproposals. Delete those first.")
            return redirect(reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug}))

        # continue with the request
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "Proposal '%s' has been deleted." % self.object.name)
        return reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug})



class SpeakerProposalDetailView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureUserOwnsProposalMixin, EnsureCFPOpenMixin, DetailView):
    model = models.SpeakerProposal
    template_name = 'speakerproposal_detail.html'


###################################################################################################
# eventproposal views


class EventProposalTypeSelectView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureCFPOpenMixin, ListView):
    """
    This view is for selecting the type of event to submit (when adding a new eventproposal to an existing speakerproposal)
    """
    model = models.EventType
    template_name = 'event_type_select.html'

    def dispatch(self, request, *args, **kwargs):
        """ Get the speakerproposal object """
        self.speaker = get_object_or_404(models.SpeakerProposal, pk=kwargs['speaker_uuid'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        """ We only allow submissions of events with EventTypes where public=True """
        return super().get_queryset().filter(public=True)

    def get_context_data(self, *args, **kwargs):
        """ Make speakerproposal object available in template """
        context = super().get_context_data(**kwargs)
        context['speaker'] = self.speaker
        return context


class EventProposalSelectPersonView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureCFPOpenMixin, ListView):
    """
    This view is for selecting an existing speakerproposal to add to an existing eventproposal
    """
    model = models.SpeakerProposal
    template_name = 'event_proposal_select_person.html'

    def dispatch(self, request, *args, **kwargs):
        """ Get EventProposal from url kwargs """
        self.eventproposal = get_object_or_404(models.EventProposal, pk=kwargs['event_uuid'], user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        """ Filter out any speakerproposals already added to this eventproposal """
        return self.eventproposal.get_available_speakerproposals().all()

    def get_context_data(self, *args, **kwargs):
        """ Make eventproposal object available in template """
        context = super().get_context_data(**kwargs)
        context['eventproposal'] = self.eventproposal
        return context


class EventProposalAddPersonView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureCFPOpenMixin, UpdateView):
    """
    This view is for adding an existing speakerproposal to an existing eventproposal
    """
    model = models.EventProposal
    template_name = 'event_proposal_add_person.html'
    fields = []
    pk_url_kwarg = 'event_uuid'

    def dispatch(self, request, *args, **kwargs):
        """ Get the speakerproposal object """
        self.speakerproposal = get_object_or_404(models.SpeakerProposal, pk=kwargs['speaker_uuid'], user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """ Make speakerproposal object available in template """
        context = super().get_context_data(**kwargs)
        context['speakerproposal'] = self.speakerproposal
        return context

    def form_valid(self, form):
        form.instance.speakers.add(self.speakerproposal)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug})


class EventProposalRemovePersonView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureCFPOpenMixin, UpdateView):
    """
    This view is for removing a speakerproposal from an existing eventproposal
    """
    model = models.EventProposal
    template_name = 'event_proposal_remove_person.html'
    fields = []
    pk_url_kwarg = 'event_uuid'

    def dispatch(self, request, *args, **kwargs):
        """ Get the speakerproposal object and check a few things """
        # get the speakerproposal object from URL kwargs
        self.speakerproposal = get_object_or_404(models.SpeakerProposal, pk=kwargs['speaker_uuid'], user=request.user)
        # run the super() dispatch method so we have self.camp otherwise the .all() lookup below craps out
        response = super().dispatch(request, *args, **kwargs)

        # is this speakerproposal even in use on this eventproposal
        if self.speakerproposal not in self.get_object().speakers.all():
            # this speaker is not associated with this event
            raise Http404

        # all good
        return response

    def get_context_data(self, *args, **kwargs):
        """ Make speakerproposal object available in template """
        context = super().get_context_data(**kwargs)
        context['speakerproposal'] = self.speakerproposal
        return context

    def form_valid(self, form):
        """ Remove the speaker from the event """
        if self.speakerproposal not in self.get_object().speakers.all():
            # this speaker is not associated with this event
            raise Http404

        if self.get_object().speakers.count() == 1:
            messages.error(self.request, "Cannot delete the last person associalted with event!")
            return redirect(reverse(
                'program:eventproposal_detail', kwargs={
                'camp_slug': self.camp.slug,
                'pk': self.get_object().uuid
            }))

        form.instance.speakers.remove(self.speakerproposal)
        return redirect(self.get_success_url())

    def get_success_url(self):
        messages.success(self.request, "Speaker %s has been removed from %s" % (
            self.speakerproposal.name,
            self.get_object().title
        ))
        return reverse(
            'program:eventproposal_detail', kwargs={
            'camp_slug': self.camp.slug,
            'pk': self.get_object().uuid
        })


class EventProposalCreateView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureCFPOpenMixin, CreateView):
    """
    This view allows a user to create a new eventproposal linked to an existing speakerproposal
    """
    model = models.EventProposal
    template_name = 'eventproposal_form.html'

    def get_form_class(self):
        """ Get the appropriate form class based on the eventtype """
        return get_eventproposal_form_class(self.event_type)

    def dispatch(self, request, *args, **kwargs):
        """ Get the speakerproposal object """
        self.speakerproposal = get_object_or_404(models.SpeakerProposal, pk=self.kwargs['speaker_uuid'])
        self.event_type = get_object_or_404(models.EventType, slug=self.kwargs['event_type_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """ Make speakerproposal object available in template """
        context = super().get_context_data(**kwargs)
        context['speaker'] = self.speakerproposal
        context['event_type'] = self.event_type
        return context

    def get_form(self):
        """
        Override get_form() method so we can set the queryset for the track selector.
        Usually this kind of thing would go into get_initial() but that does not work for some reason, so we do it here instead.
        """
        form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs())
        form.fields['track'].queryset = models.EventTrack.objects.filter(camp=self.camp)
        return form


    def form_valid(self, form):
        # set camp and user for this eventproposal
        eventproposal = form.save(commit=False)
        eventproposal.user = self.request.user
        eventproposal.event_type = self.event_type
        eventproposal.save()

        # add the speakerproposal to the eventproposal
        eventproposal.speakers.add(self.speakerproposal)

        # all good
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug})


class EventProposalUpdateView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureUserOwnsProposalMixin, EnsureCFPOpenMixin, UpdateView):
    model = models.EventProposal
    template_name = 'eventproposal_form.html'

    def get_form_class(self):
        """ Get the appropriate form class based on the eventtype """
        return get_eventproposal_form_class(self.get_object().event_type)

    def get_success_url(self):
        return reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug})

    def get_context_data(self, *args, **kwargs):
        """ Make speakerproposal and eventtype objects available in the template """
        context = super().get_context_data(**kwargs)
        context['event_type'] = self.get_object().event_type
        return context

    def get_form(self):
        """
        Override get_form() method so we can set the queryset for the track selector.
        Usually this kind of thing would go into get_initial() but that does not work for some reason, so we do it here instead.
        """
        form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs())
        form.fields['track'].queryset = models.EventTrack.objects.filter(camp=self.camp)
        return form


class EventProposalDeleteView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureUserOwnsProposalMixin, EnsureCFPOpenMixin, DeleteView):
    model = models.EventProposal
    template_name = 'proposal_delete.html'

    def get_success_url(self):
        messages.success(self.request, "Proposal '%s' has been deleted." % self.object.title)
        return reverse('program:proposal_list', kwargs={'camp_slug': self.camp.slug})


class EventProposalDetailView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureUserOwnsProposalMixin, EnsureCFPOpenMixin, DetailView):
    model = models.EventProposal
    template_name = 'eventproposal_detail.html'

###################################################################################################
# combined proposal views


class CombinedProposalTypeSelectView(LoginRequiredMixin, CampViewMixin, ListView):
    """
    A view which allows the user to select event type without anything else on the page
    """
    model = models.EventType
    template_name = 'event_type_select.html'

    def get_queryset(self, **kwargs):
        """ We only allow submissions of events with EventTypes where public=True """
        return super().get_queryset().filter(public=True)


class CombinedProposalPersonSelectView(LoginRequiredMixin, CampViewMixin, ListView):
    """
    A view which allows the user to 1) choose between existing SpeakerProposals or
    2) pressing a button to create a new SpeakerProposal.
    Redirect straight to 2) if no existing SpeakerProposals exist.
    """
    model = models.SpeakerProposal
    template_name = 'combined_proposal_select_person.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Check that we have a valid EventType
        """
        # get EventType from url kwargs
        self.eventtype = get_object_or_404(models.EventType, slug=self.kwargs['event_type_slug'])

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        # only show speaker proposals for the current user
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """
        Add EventType to template context
        """
        context = super().get_context_data(**kwargs)
        context['eventtype'] = self.eventtype
        return context

    def get(self, request, *args, **kwargs):
        """ If we don't have any existing SpeakerProposals just redirect directly to the combined submit view """
        if not self.get_queryset().exists():
            return redirect(reverse_lazy('program:proposal_combined_submit', kwargs={'camp_slug': self.camp.slug, 'event_type_slug': self.eventtype.slug}))
        return super().get(request, *args, **kwargs)


class CombinedProposalSubmitView(LoginRequiredMixin, CampViewMixin, CreateView):
    """
    This view is used by users to submit CFP proposals.
    It allows the user to submit an EventProposal and a SpeakerProposal together.
    It can also be used with a preselected SpeakerProposal uuid in url kwargs
    """
    template_name = 'combined_proposal_submit.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Check that we have a valid EventType
        """
        # get EventType from url kwargs
        self.eventtype = get_object_or_404(models.EventType, slug=self.kwargs['event_type_slug'])

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Add EventType to template context
        """
        context = super().get_context_data(**kwargs)
        context['eventtype'] = self.eventtype
        return context

    def form_valid(self, form):
        """
        Save the object(s) here before redirecting
        """
        if hasattr(self, 'speakerproposal'):
            eventproposal = form.save(commit=False)
            eventproposal.user = self.request.user
            eventproposal.event_type = self.eventtype
            eventproposal.save()
            eventproposal.speakers.add(self.speakerproposal)
        else:
            # first save the SpeakerProposal
            speakerproposal = form['speakerproposal'].save(commit=False)
            speakerproposal.camp = self.camp
            speakerproposal.user = self.request.user
            speakerproposal.save()

            # then save the eventproposal
            eventproposal = form['eventproposal'].save(commit=False)
            eventproposal.user = self.request.user
            eventproposal.event_type = self.eventtype
            eventproposal.save()

            # add the speakerproposal to the eventproposal
            eventproposal.speakers.add(speakerproposal)

        # all good
        return redirect(reverse_lazy('program:proposal_list', kwargs={'camp_slug': self.camp.slug}))

    def get_form_class(self):
        """
        Unless we have an existing SpeakerProposal we must show two forms on the page.
        We use betterforms.MultiModelForm to combine two forms on the page
        """
        if hasattr(self, 'speakerproposal'):
            # we already have a speakerproposal, just show an eventproposal form
            return get_eventproposal_form_class(eventtype=self.eventtype)

        # get the two forms we need to build the MultiModelForm
        SpeakerProposalForm = get_speakerproposal_form_class(eventtype=self.eventtype)
        EventProposalForm = get_eventproposal_form_class(eventtype=self.eventtype)

        # build our MultiModelForm
        class CombinedProposalSubmitForm(MultiModelForm):
            form_classes = OrderedDict((
                ('speakerproposal', SpeakerProposalForm),
                ('eventproposal', EventProposalForm),
            ))

        # return the form class
        return CombinedProposalSubmitForm

    def get_form(self):
        """
        Override get_form() method so we can set the queryset for the track selector.
        Usually this kind of thing would go into get_initial() but that does not work for some reason, so we do it here instead.
        """
        form_class = self.get_form_class()
        form = form_class(**self.get_form_kwargs())
        form.forms['eventproposal'].fields['track'].queryset = models.EventTrack.objects.filter(camp=self.camp)
        return form


###################################################################################################
# speaker views


class SpeakerDetailView(CampViewMixin, DetailView):
    model = models.Speaker
    template_name = 'speaker_detail.html'


class SpeakerListView(CampViewMixin, ListView):
    model = models.Speaker
    template_name = 'speaker_list.html'


###################################################################################################
# event views


class EventListView(CampViewMixin, ListView):
    model = models.Event
    template_name = 'event_list.html'


class EventDetailView(CampViewMixin, DetailView):
    model = models.Event
    template_name = 'schedule_event_detail.html'


###################################################################################################
# schedule views


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
        context['schedule_midnight_offset_hours'] = settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS
        return context


class CallForParticipationView(CampViewMixin, TemplateView):
    template_name = 'call_for_participation.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.camp.call_for_participation:
            context['cfp_markdown'] = self.camp.call_for_participation
        else:
            context['cfp_markdown'] = "<p class='lead'>This CFP has not been written yet.</p>"
        return context


###################################################################################################
# control center csv


class ProgramControlCenter(CampViewMixin, TemplateView):
    template_name = "control/index.html"

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        proposals = models.EventProposal.objects.filter(
            camp=self.camp
        ).select_related('user', 'event')
        context['proposals'] = proposals

        engine = Engine.get_default()
        template = engine.get_template('control/proposal_overview.csv')
        csv = template.render(Context(context))
        context['csv'] = csv

        return context

###################################################################################################
# URL views

class UrlCreateView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureCFPOpenMixin, UrlViewMixin, CreateView):
    model = models.Url
    template_name = 'url_form.html'
    fields = ['urltype', 'url']

    def form_valid(self, form):
        """
        Set the proposal FK before saving
        """
        if hasattr(self, 'eventproposal') and self.eventproposal:
            form.instance.eventproposal = self.eventproposal
            url = form.save()
        else:
            form.instance.speakerproposal = self.speakerproposal
            url = form.save()

        messages.success(self.request, "URL saved.")

        # all good
        return redirect(self.get_success_url())


class UrlUpdateView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureCFPOpenMixin, UrlViewMixin, UpdateView):
    model = models.Url
    template_name = 'url_form.html'
    fields = ['urltype', 'url']
    pk_url_kwarg = 'url_uuid'


class UrlDeleteView(LoginRequiredMixin, CampViewMixin, EnsureWritableCampMixin, EnsureCFPOpenMixin, UrlViewMixin, DeleteView):
    model = models.Url
    template_name = 'url_delete.html'
    pk_url_kwarg = 'url_uuid'

