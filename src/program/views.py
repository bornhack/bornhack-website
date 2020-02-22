import logging
from collections import OrderedDict

import icalendar
from camps.mixins import CampViewMixin
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect
from django.template import Context, Engine
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from lxml import etree, objectify
from utils.middleware import RedirectException
from utils.mixins import UserIsObjectOwnerMixin

from . import models
from .email import (
    add_eventproposal_updated_email,
    add_new_eventproposal_email,
    add_new_speakerproposal_email,
    add_speakerproposal_updated_email,
)
from .forms import EventProposalForm, SpeakerProposalForm
from .mixins import (
    EnsureCFPOpenMixin,
    EnsureUserOwnsProposalMixin,
    EnsureWritableCampMixin,
    EventFeedbackViewMixin,
    EventViewMixin,
    UrlViewMixin,
)
from .multiform import MultiModelForm

logger = logging.getLogger("bornhack.%s" % __name__)


###################################################################################################
# ical calendar


class ICSView(CampViewMixin, View):
    def get(self, request, *args, **kwargs):
        eventinstances = models.EventInstance.objects.filter(
            event__track__camp=self.camp
        )

        # Type query
        type_query = request.GET.get("type", None)
        if type_query:
            type_slugs = type_query.split(",")
            types = models.EventType.objects.filter(slug__in=type_slugs)
            eventinstances = eventinstances.filter(event__event_type__in=types)

        # Location query
        location_query = request.GET.get("location", None)
        if location_query:
            location_slugs = location_query.split(",")
            locations = models.EventLocation.objects.filter(
                slug__in=location_slugs, camp=self.camp
            )
            eventinstances = eventinstances.filter(location__in=locations)

        # Video recording query
        video_query = request.GET.get("video", None)
        if video_query:
            video_states = video_query.split(",")
            query_kwargs = {}

            if "has-recording" in video_states:
                query_kwargs["event__video_url__isnull"] = False

            if "to-be-recorded" in video_states:
                query_kwargs["event__video_recording"] = True

            if "not-to-be-recorded" in video_states:
                if "event__video_recording" in query_kwargs:
                    del query_kwargs["event__video_recording"]
                else:
                    query_kwargs["event__video_recording"] = False

            eventinstances = eventinstances.filter(**query_kwargs)

        cal = icalendar.Calendar()
        for event_instance in eventinstances:
            cal.add_component(event_instance.get_ics_event())

        response = HttpResponse(cal.to_ical())
        response["Content-Type"] = "text/calendar"
        response["Content-Disposition"] = "inline; filename={}.ics".format(
            self.camp.slug
        )
        return response


###################################################################################################
# proposals list view


class ProposalListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = models.SpeakerProposal
    template_name = "proposal_list.html"
    context_object_name = "speakerproposal_list"

    def get_queryset(self, **kwargs):
        # only show speaker proposals for the current user
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # also add eventproposals to the context
        context["eventproposal_list"] = models.EventProposal.objects.filter(
            track__camp=self.camp, user=self.request.user
        )
        context["eventtype_list"] = models.EventType.objects.filter(public=True)
        return context


###################################################################################################
# speakerproposal views


class SpeakerProposalCreateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    CreateView,
):
    """ This view allows a user to create a new SpeakerProposal linked to an existing EventProposal """

    model = models.SpeakerProposal
    template_name = "speakerproposal_form.html"
    form_class = SpeakerProposalForm

    def dispatch(self, request, *args, **kwargs):
        """ Get the eventproposal object """
        self.eventproposal = get_object_or_404(
            models.EventProposal, pk=kwargs["event_uuid"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})

    def get_form_kwargs(self):
        """
        Set camp and eventtype for the form
        """
        kwargs = super().get_form_kwargs()
        kwargs.update({"camp": self.camp, "eventtype": self.eventproposal.event_type})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["eventproposal"] = self.eventproposal
        return context

    def form_valid(self, form):
        # set user before saving
        form.instance.user = self.request.user
        form.instance.camp = self.camp

        if not form.instance.email:
            form.instance.email = self.request.user.email

        speakerproposal = form.save()

        # add speakerproposal to eventproposal
        self.eventproposal.speakers.add(speakerproposal)

        # send mail to content team
        if not add_new_speakerproposal_email(speakerproposal):
            logger.error(
                "Unable to send email to content team after new speakerproposal"
            )

        return redirect(
            reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})
        )


class SpeakerProposalUpdateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureUserOwnsProposalMixin,
    EnsureCFPOpenMixin,
    UpdateView,
):
    """
    This view allows a user to update an existing SpeakerProposal.
    """

    model = models.SpeakerProposal
    template_name = "speakerproposal_form.html"
    form_class = SpeakerProposalForm

    def get_form_kwargs(self):
        """
        Set camp and eventtype for the form
        """
        kwargs = super().get_form_kwargs()
        if self.get_object().eventproposals.count() == 1:
            # determine which form to use based on the type of event associated with the proposal
            eventtype = self.get_object().eventproposals.get().event_type
        else:
            # more than one eventproposal. If all events are the same type we can still show a non-generic form here
            eventtypes = set()
            for ep in self.get_object().eventproposals.all():
                eventtypes.add(ep.event_type)
            if len(eventtypes) == 1:
                # only one eventtype found
                eventtype = ep.event_type
            else:
                # more than one type of event for this person, return the generic speakerproposal form
                eventtype = None

        # add camp and eventtype to form kwargs
        kwargs.update({"camp": self.camp, "eventtype": eventtype})

        return kwargs

    def form_valid(self, form):
        """
        Change the speakerproposal status to pending
        """
        # set proposal status to pending
        form.instance.proposal_status = models.SpeakerProposal.PROPOSAL_PENDING
        speakerproposal = form.save()

        # send mail to content team
        if not add_speakerproposal_updated_email(speakerproposal):
            logger.error(
                "Unable to send email to content team after speakerproposal update"
            )

        # message user and redirect
        messages.info(
            self.request, "Your proposal is now pending approval by the content team."
        )
        return redirect(
            reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})
        )


class SpeakerProposalDeleteView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureUserOwnsProposalMixin,
    EnsureCFPOpenMixin,
    DeleteView,
):
    """
    This view allows a user to delete an existing SpeakerProposal object, as long as it is not linked to any EventProposals
    """

    model = models.SpeakerProposal
    template_name = "proposal_delete.html"

    def get(self, request, *args, **kwargs):
        # do not permit deleting if this speakerproposal is linked to any eventproposals
        if self.get_object().eventproposals.exists():
            messages.error(
                request,
                "Cannot delete a person while it is associated with one or more eventproposals. Delete those first.",
            )
            return redirect(
                reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})
            )

        # continue with the request
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request, "Proposal '%s' has been deleted." % self.object.name
        )
        return reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})


class SpeakerProposalDetailView(
    LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, DetailView
):
    model = models.SpeakerProposal
    template_name = "speakerproposal_detail.html"


###################################################################################################
# eventproposal views


class EventProposalTypeSelectView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    ListView,
):
    """
    This view is for selecting the type of event to submit (when adding a new eventproposal to an existing speakerproposal)
    """

    model = models.EventType
    template_name = "event_type_select.html"

    def dispatch(self, request, *args, **kwargs):
        """ Get the speakerproposal object """
        self.speaker = get_object_or_404(
            models.SpeakerProposal, pk=kwargs["speaker_uuid"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        """ We only allow submissions of events with EventTypes where public=True """
        return super().get_queryset().filter(public=True)

    def get_context_data(self, *args, **kwargs):
        """ Make speakerproposal object available in template """
        context = super().get_context_data(**kwargs)
        context["speaker"] = self.speaker
        return context


class EventProposalSelectPersonView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    ListView,
):
    """
    This view is for selecting an existing speakerproposal to add to an existing eventproposal
    """

    model = models.SpeakerProposal
    template_name = "event_proposal_select_person.html"

    def dispatch(self, request, *args, **kwargs):
        """ Get EventProposal from url kwargs """
        self.eventproposal = get_object_or_404(
            models.EventProposal, pk=kwargs["event_uuid"], user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        """ Filter out any speakerproposals already added to this eventproposal """
        return self.eventproposal.get_available_speakerproposals().all()

    def get_context_data(self, *args, **kwargs):
        """ Make eventproposal object available in template """
        context = super().get_context_data(**kwargs)
        context["eventproposal"] = self.eventproposal
        return context


class EventProposalAddPersonView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UpdateView,
):
    """
    This view is for adding an existing speakerproposal to an existing eventproposal
    """

    model = models.EventProposal
    template_name = "event_proposal_add_person.html"
    fields = []
    pk_url_kwarg = "event_uuid"

    def dispatch(self, request, *args, **kwargs):
        """ Get the speakerproposal object """
        self.speakerproposal = get_object_or_404(
            models.SpeakerProposal, pk=kwargs["speaker_uuid"], user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """ Make speakerproposal object available in template """
        context = super().get_context_data(**kwargs)
        context["speakerproposal"] = self.speakerproposal
        return context

    def form_valid(self, form):
        form.instance.speakers.add(self.speakerproposal)
        messages.success(
            self.request,
            "%s has been added as %s for %s"
            % (
                self.speakerproposal.name,
                form.instance.event_type.host_title,
                form.instance.title,
            ),
        )
        return redirect(self.get_success_url())


class EventProposalRemovePersonView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UpdateView,
):
    """
    This view is for removing a speakerproposal from an existing eventproposal
    """

    model = models.EventProposal
    template_name = "event_proposal_remove_person.html"
    fields = []
    pk_url_kwarg = "event_uuid"

    def dispatch(self, request, *args, **kwargs):
        """ Get the speakerproposal object and check a few things """
        # get the speakerproposal object from URL kwargs
        self.speakerproposal = get_object_or_404(
            models.SpeakerProposal, pk=kwargs["speaker_uuid"], user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """ Make speakerproposal object available in template """
        context = super().get_context_data(**kwargs)
        context["speakerproposal"] = self.speakerproposal
        return context

    def form_valid(self, form):
        """ Remove the speaker from the event """
        if self.speakerproposal not in self.get_object().speakers.all():
            # this speaker is not associated with this event
            raise Http404

        if self.get_object().speakers.count() == 1:
            messages.error(
                self.request, "Cannot delete the last person associalted with event!"
            )
            return redirect(self.get_success_url())

        # remove speakerproposal from eventproposal
        form.instance.speakers.remove(self.speakerproposal)
        messages.success(
            self.request,
            "%s has been removed from %s"
            % (self.speakerproposal.name, self.get_object().title),
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "program:eventproposal_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.get_object().uuid},
        )


class EventProposalCreateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    CreateView,
):
    """
    This view allows a user to create a new eventproposal linked to an existing speakerproposal
    """

    model = models.EventProposal
    template_name = "eventproposal_form.html"
    form_class = EventProposalForm

    def dispatch(self, request, *args, **kwargs):
        """ Get the speakerproposal object """
        self.speakerproposal = get_object_or_404(
            models.SpeakerProposal, pk=self.kwargs["speaker_uuid"]
        )
        self.event_type = get_object_or_404(
            models.EventType, slug=self.kwargs["event_type_slug"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """ Make speakerproposal object available in template """
        context = super().get_context_data(**kwargs)
        context["speaker"] = self.speakerproposal
        context["event_type"] = self.event_type
        return context

    def get_form_kwargs(self):
        """
        Set camp and eventtype for the form
        """
        kwargs = super().get_form_kwargs()
        kwargs.update({"camp": self.camp, "eventtype": self.event_type})
        return kwargs

    def form_valid(self, form):
        # set camp and user for this eventproposal
        eventproposal = form.save(user=self.request.user, event_type=self.event_type)

        # add the speakerproposal to the eventproposal
        eventproposal.speakers.add(self.speakerproposal)

        # send mail to content team
        if not add_new_eventproposal_email(eventproposal):
            logger.error("Unable to send email to content team after new eventproposal")

        # all good
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})


class EventProposalUpdateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureUserOwnsProposalMixin,
    EnsureCFPOpenMixin,
    UpdateView,
):
    model = models.EventProposal
    template_name = "eventproposal_form.html"
    form_class = EventProposalForm

    def get_form_kwargs(self):
        """
        Set camp and eventtype for the form
        """
        kwargs = super().get_form_kwargs()
        kwargs.update({"camp": self.camp, "eventtype": self.get_object().event_type})
        return kwargs

    def get_context_data(self, *args, **kwargs):
        """ Make speakerproposal and eventtype objects available in the template """
        context = super().get_context_data(**kwargs)
        context["event_type"] = self.get_object().event_type
        return context

    def form_valid(self, form):
        # set status to pending and save eventproposal
        form.instance.proposal_status = models.EventProposal.PROPOSAL_PENDING
        eventproposal = form.save()

        # send email to content team
        if not add_eventproposal_updated_email(eventproposal):
            logger.error(
                "Unable to send email to content team after eventproposal update"
            )

        # message for the user and redirect
        messages.info(
            self.request, "Your proposal is now pending approval by the content team."
        )
        return redirect(
            reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})
        )


class EventProposalDeleteView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureUserOwnsProposalMixin,
    EnsureCFPOpenMixin,
    DeleteView,
):
    model = models.EventProposal
    template_name = "proposal_delete.html"

    def get_success_url(self):
        messages.success(
            self.request, "Proposal '%s' has been deleted." % self.object.title
        )
        return reverse("program:proposal_list", kwargs={"camp_slug": self.camp.slug})


class EventProposalDetailView(
    LoginRequiredMixin, CampViewMixin, EnsureUserOwnsProposalMixin, DetailView
):
    model = models.EventProposal
    template_name = "eventproposal_detail.html"


###################################################################################################
# combined proposal views


class CombinedProposalTypeSelectView(LoginRequiredMixin, CampViewMixin, ListView):
    """
    A view which allows the user to select event type without anything else on the page
    """

    model = models.EventType
    template_name = "event_type_select.html"

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
    template_name = "combined_proposal_select_person.html"

    def dispatch(self, request, *args, **kwargs):
        """
        Check that we have a valid EventType
        """
        # get EventType from url kwargs
        self.eventtype = get_object_or_404(
            models.EventType, slug=self.kwargs["event_type_slug"]
        )

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        # only show speaker proposals for the current user
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """
        Add EventType to template context
        """
        context = super().get_context_data(**kwargs)
        context["eventtype"] = self.eventtype
        return context

    def get(self, request, *args, **kwargs):
        """ If we don't have any existing SpeakerProposals just redirect directly to the combined submit view """
        if not self.get_queryset().exists():
            return redirect(
                reverse_lazy(
                    "program:proposal_combined_submit",
                    kwargs={
                        "camp_slug": self.camp.slug,
                        "event_type_slug": self.eventtype.slug,
                    },
                )
            )
        return super().get(request, *args, **kwargs)


class CombinedProposalSubmitView(LoginRequiredMixin, CampViewMixin, CreateView):
    """
    This view is used by users to submit CFP proposals.
    It allows the user to submit an EventProposal and a SpeakerProposal together.
    It can also be used with a preselected SpeakerProposal uuid in url kwargs
    """

    template_name = "combined_proposal_submit.html"

    def dispatch(self, request, *args, **kwargs):
        """
        Check that we have a valid EventType
        """
        # get EventType from url kwargs
        self.eventtype = get_object_or_404(
            models.EventType, slug=self.kwargs["event_type_slug"]
        )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Add EventType to template context
        """
        context = super().get_context_data(**kwargs)
        context["eventtype"] = self.eventtype
        return context

    def form_valid(self, form):
        """
        Save the object(s) here before redirecting
        """
        if hasattr(self, "speakerproposal"):
            eventproposal = form.save(user=self.request.user, event_type=self.eventtype)
            eventproposal.speakers.add(self.speakerproposal)
        else:
            # first save the SpeakerProposal
            speakerproposal = form["speakerproposal"].save(commit=False)
            speakerproposal.camp = self.camp
            speakerproposal.user = self.request.user
            if not speakerproposal.email:
                speakerproposal.email = self.request.user.email
            speakerproposal.save()

            # then save the eventproposal
            eventproposal = form["eventproposal"].save(
                user=self.request.user, event_type=self.eventtype
            )
            eventproposal.user = self.request.user
            eventproposal.event_type = self.eventtype
            eventproposal.save()

            # add the speakerproposal to the eventproposal
            eventproposal.speakers.add(speakerproposal)

        # send mail(s) to content team
        if not add_new_eventproposal_email(eventproposal):
            logger.error("Unable to send email to content team after new eventproposal")
        if not hasattr(self, "speakerproposal"):
            if not add_new_speakerproposal_email(speakerproposal):
                logger.error(
                    "Unable to send email to content team after new speakerproposal"
                )

        # all good
        return redirect(
            reverse_lazy("program:proposal_list", kwargs={"camp_slug": self.camp.slug})
        )

    def get_form_class(self):
        """
        Unless we have an existing SpeakerProposal we must show two forms on the page.
        We use betterforms.MultiModelForm to combine two forms on the page
        """
        if hasattr(self, "speakerproposal"):
            # we already have a speakerproposal, just show an eventproposal form
            return EventProposalForm

        # build our MultiModelForm
        class CombinedProposalSubmitForm(MultiModelForm):
            form_classes = OrderedDict(
                (
                    ("speakerproposal", SpeakerProposalForm),
                    ("eventproposal", EventProposalForm),
                )
            )

        # return the form class
        return CombinedProposalSubmitForm

    def get_form_kwargs(self):
        """
        Set camp and eventtype for the form
        """
        kwargs = super().get_form_kwargs()
        kwargs.update({"camp": self.camp, "eventtype": self.eventtype})
        return kwargs


###################################################################################################
# speaker views


class SpeakerDetailView(CampViewMixin, DetailView):
    model = models.Speaker
    template_name = "speaker_detail.html"


class SpeakerListView(CampViewMixin, ListView):
    model = models.Speaker
    template_name = "speaker_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("events")
        qs = qs.prefetch_related("events__event_type")
        return qs


###################################################################################################
# event views


class EventListView(CampViewMixin, ListView):
    model = models.Event
    template_name = "event_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("event_type", "track", "instances", "speakers")
        return qs


class EventDetailView(CampViewMixin, DetailView):
    model = models.Event
    template_name = "schedule_event_detail.html"
    slug_url_kwarg = "event_slug"


###################################################################################################
# schedule views


class NoScriptScheduleView(CampViewMixin, TemplateView):
    template_name = "noscript_schedule_view.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["eventinstances"] = models.EventInstance.objects.filter(
            event__track__camp=self.camp
        ).order_by("when")
        return context


class ScheduleView(CampViewMixin, TemplateView):
    template_name = "schedule_overview.html"

    def dispatch(self, request, *args, **kwargs):
        """
        If no events are scheduled redirect to the event page
        """
        response = super().dispatch(request, *args, **kwargs)

        events_exist = models.EventInstance.objects.filter(
            event__track__camp=self.camp
        ).exists()

        redirect_to_event_list = False

        if not events_exist:
            redirect_to_event_list = True

        if not self.camp.show_schedule and not request.user.is_superuser:
            redirect_to_event_list = True

        if redirect_to_event_list:
            return redirect(
                reverse("program:event_index", kwargs={"camp_slug": self.camp.slug})
            )

        return response

    def get_context_data(self, *args, **kwargs):
        context = super(ScheduleView, self).get_context_data(**kwargs)
        context[
            "schedule_midnight_offset_hours"
        ] = settings.SCHEDULE_MIDNIGHT_OFFSET_HOURS
        return context


class CallForParticipationView(CampViewMixin, TemplateView):
    template_name = "call_for_participation.html"


class FrabXmlView(CampViewMixin, View):
    """
    This view returns an XML schedule in Frab format
    XSD is from https://raw.githubusercontent.com/wiki/frab/frab/images/schedule.xsd
    """

    def get(self, *args, **kwargs):
        qs = models.EventInstance.objects.filter(event__track__camp=self.camp).order_by(
            "when", "location"
        )
        E = objectify.ElementMaker(annotate=False)
        days = ()
        i = 0
        for day in self.camp.get_days("camp")[:-1]:
            i += 1
            locations = ()
            for location in models.EventLocation.objects.filter(
                id__in=qs.values_list("location_id", flat=True)
            ):
                instances = ()
                for instance in qs.filter(when__contained_by=day, location=location):
                    speakers = ()
                    for speaker in instance.event.speakers.all():
                        speakers += (E.person(speaker.name, id=str(speaker.pk)),)
                    urls = ()
                    for url in instance.event.urls.all():
                        urls += (E.link(url.urltype.name, href=url.url),)
                    instances += (
                        E.event(
                            E.date(instance.when.lower.isoformat()),
                            E.start(instance.when.lower.time()),
                            E.duration(instance.when.upper - instance.when.lower),
                            E.room(location.name),
                            E.slug(f"{instance.pk}-{instance.event.slug}"),
                            E.url(
                                self.request.build_absolute_uri(
                                    instance.event.get_absolute_url()
                                )
                            ),
                            E.recording(
                                E.license("CC BY-SA 4.0"),
                                E.optout(
                                    "false"
                                    if instance.event.video_recording
                                    else "true"
                                ),
                            ),
                            E.title(instance.event.title),
                            E.subtitle(""),
                            E.track(instance.event.track),
                            E.type(instance.event.event_type),
                            E.language("en"),
                            E.abstract(instance.event.abstract),
                            E.description(""),
                            E.persons(*speakers),
                            E.links(*urls),
                            E.attachments,
                            id=str(instance.id),
                            guid=str(instance.uuid),
                        ),
                    )
                if instances:
                    locations += (E.room(*instances, name=location.name),)
            days += (
                E.day(
                    *locations,
                    index=str(i),
                    date=str(day.lower.date()),
                    start=day.lower.isoformat(),
                    end=day.upper.isoformat(),
                ),
            )

        xml = E.schedule(
            E.version("BornHack Frab XML Generator v1.0"),
            E.conference(
                E.title(self.camp.title),
                E.acronym(str(self.camp.camp.lower.year)),
                E.start(self.camp.camp.lower.date().isoformat()),
                E.end(self.camp.camp.upper.date().isoformat()),
                E.days(len(self.camp.get_days("camp"))),
                E.timeslot_duration("00:30"),
                E.base_url(self.request.build_absolute_uri("/")),
            ),
            *days,
        )
        xml = etree.tostring(xml, pretty_print=True, xml_declaration=True)

        # let's play nice - validate the XML before returning it
        schema = etree.XMLSchema(file="program/xsd/schedule.xml.xsd")
        parser = objectify.makeparser(schema=schema)
        try:
            _ = objectify.fromstring(xml, parser)
        except etree.XMLSyntaxError:
            # we are generating invalid XML
            logger.exception("Something went sideways when validating frab xml :(")
            return HttpResponseServerError()
        response = HttpResponse(content_type="application/xml")
        response.write(xml)
        return response


###################################################################################################
# control center csv


class ProgramControlCenter(CampViewMixin, TemplateView):
    template_name = "control/index.html"

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        proposals = models.EventProposal.objects.filter(camp=self.camp).select_related(
            "user", "event"
        )
        context["proposals"] = proposals

        engine = Engine.get_default()
        template = engine.get_template("control/proposal_overview.csv")
        csv = template.render(Context(context))
        context["csv"] = csv

        return context


###################################################################################################
# URL views


class UrlCreateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UrlViewMixin,
    CreateView,
):
    model = models.Url
    template_name = "url_form.html"
    fields = ["urltype", "url"]

    def form_valid(self, form):
        """
        Set the proposal FK before saving
        Set proposal as pending if it isn't already
        """
        if hasattr(self, "eventproposal") and self.eventproposal:
            # this URL belongs to an eventproposal
            form.instance.eventproposal = self.eventproposal
            form.save()
            if (
                self.eventproposal.proposal_status
                != models.SpeakerProposal.PROPOSAL_PENDING
            ):
                self.eventproposal.proposal_status = (
                    models.SpeakerProposal.PROPOSAL_PENDING
                )
                self.eventproposal.save()
                messages.success(
                    self.request,
                    "%s is now pending review by the Content Team."
                    % self.eventproposal.title,
                )
        else:
            # this URL belongs to a speakerproposal
            form.instance.speakerproposal = self.speakerproposal
            form.save()
            if (
                self.speakerproposal.proposal_status
                != models.SpeakerProposal.PROPOSAL_PENDING
            ):
                self.speakerproposal.proposal_status = (
                    models.SpeakerProposal.PROPOSAL_PENDING
                )
                self.speakerproposal.save()
                messages.success(
                    self.request,
                    "%s is now pending review by the Content Team."
                    % self.speakerproposal.name,
                )

        messages.success(self.request, "URL saved.")

        # all good
        return redirect(
            reverse_lazy("program:proposal_list", kwargs={"camp_slug": self.camp.slug})
        )


class UrlUpdateView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UrlViewMixin,
    UpdateView,
):
    model = models.Url
    template_name = "url_form.html"
    fields = ["urltype", "url"]
    pk_url_kwarg = "url_uuid"

    def form_valid(self, form):
        """
        Set proposal as pending if it isn't already
        """
        if hasattr(self, "eventproposal") and self.eventproposal:
            # this URL belongs to a speakerproposal
            form.save()
            if (
                self.eventproposal.proposal_status
                != models.SpeakerProposal.PROPOSAL_PENDING
            ):
                self.eventproposal.proposal_status = (
                    models.SpeakerProposal.PROPOSAL_PENDING
                )
                self.eventproposal.save()
                messages.success(
                    self.request,
                    "%s is now pending review by the Content Team."
                    % self.eventproposal.title,
                )
        else:
            # this URL belongs to a speakerproposal
            form.save()
            if (
                self.speakerproposal.proposal_status
                != models.SpeakerProposal.PROPOSAL_PENDING
            ):
                self.speakerproposal.proposal_status = (
                    models.SpeakerProposal.PROPOSAL_PENDING
                )
                self.speakerproposal.save()
                messages.success(
                    self.request,
                    "%s is now pending review by the Content Team."
                    % self.speakerproposal.name,
                )

        messages.success(self.request, "URL saved.")

        # all good
        return redirect(
            reverse_lazy("program:proposal_list", kwargs={"camp_slug": self.camp.slug})
        )


class UrlDeleteView(
    LoginRequiredMixin,
    CampViewMixin,
    EnsureWritableCampMixin,
    EnsureCFPOpenMixin,
    UrlViewMixin,
    DeleteView,
):
    model = models.Url
    template_name = "url_delete.html"
    pk_url_kwarg = "url_uuid"

    def delete(self, request, *args, **kwargs):
        """
        Set proposal as pending if it isn't already
        """
        if hasattr(self, "eventproposal") and self.eventproposal:
            # this URL belongs to a speakerproposal
            if (
                self.eventproposal.proposal_status
                != models.SpeakerProposal.PROPOSAL_PENDING
            ):
                self.eventproposal.proposal_status = (
                    models.SpeakerProposal.PROPOSAL_PENDING
                )
                self.eventproposal.save()
                messages.success(
                    self.request,
                    "%s is now pending review by the Content Team."
                    % self.eventproposal.title,
                )
        else:
            # this URL belongs to a speakerproposal
            if (
                self.speakerproposal.proposal_status
                != models.SpeakerProposal.PROPOSAL_PENDING
            ):
                self.speakerproposal.proposal_status = (
                    models.SpeakerProposal.PROPOSAL_PENDING
                )
                self.speakerproposal.save()
                messages.success(
                    self.request,
                    "%s is now pending review by the Content Team."
                    % self.speakerproposal.name,
                )

        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, "URL deleted.")

        # all good
        return redirect(
            reverse_lazy("program:proposal_list", kwargs={"camp_slug": self.camp.slug})
        )


###################################################################################################
# Feedback views


class FeedbackListView(LoginRequiredMixin, EventViewMixin, ListView):
    """
    The FeedbackListView is used by the event owner to see approved Feedback for the Event.
    """

    model = models.EventFeedback
    template_name = "eventfeedback_list.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        if not self.event.proposal or not self.event.proposal.user == self.request.user:
            messages.error(self.request, "Only the event owner can read feedback!")
            raise RedirectException(
                reverse(
                    "program:event_detail",
                    kwargs={"camp_slug": self.camp.slug, "event_slug": self.event.slug},
                )
            )

    def get_queryset(self, *args, **kwargs):
        return models.EventFeedback.objects.filter(event=self.event, approved=True)


class FeedbackCreateView(LoginRequiredMixin, EventViewMixin, CreateView):
    """
    Used by users to create Feedback for an Event. Available to all logged in users.
    """

    model = models.EventFeedback
    fields = ["expectations_fulfilled", "attend_speaker_again", "rating", "comment"]
    template_name = "eventfeedback_form.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        if models.EventFeedback.objects.filter(
            event=self.event, user=self.request.user
        ).exists():
            raise RedirectException(
                reverse(
                    "program:eventfeedback_detail",
                    kwargs={"camp_slug": self.camp.slug, "event_slug": self.event.slug},
                )
            )

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["expectations_fulfilled"].widget = forms.RadioSelect(
            choices=models.EventFeedback.YESNO_CHOICES,
        )
        form.fields["attend_speaker_again"].widget = forms.RadioSelect(
            choices=models.EventFeedback.YESNO_CHOICES,
        )
        form.fields["rating"].widget = forms.RadioSelect(
            choices=models.EventFeedback.RATING_CHOICES,
        )
        return form

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.user = self.request.user
        feedback.event = self.event
        feedback.save()
        messages.success(
            self.request, "Your feedback was submitted, it is now pending approval."
        )
        return redirect(feedback.get_absolute_url())


class FeedbackDetailView(
    LoginRequiredMixin, EventFeedbackViewMixin, UserIsObjectOwnerMixin, DetailView
):
    """
    Used by the EventFeedback owner to see their own feedback.
    """

    model = models.EventFeedback
    template_name = "eventfeedback_detail.html"


class FeedbackUpdateView(
    LoginRequiredMixin, EventFeedbackViewMixin, UserIsObjectOwnerMixin, UpdateView
):
    """
    Used by the EventFeedback owner to update their feedback.
    """

    model = models.EventFeedback
    fields = ["expectations_fulfilled", "attend_speaker_again", "rating", "comment"]
    template_name = "eventfeedback_form.html"

    def form_valid(self, form):
        feedback = form.save(commit=False)
        feedback.approved = False
        feedback.save()
        messages.success(self.request, "Your feedback was updated")
        return redirect(feedback.get_absolute_url())


class FeedbackDeleteView(
    LoginRequiredMixin, EventFeedbackViewMixin, UserIsObjectOwnerMixin, DeleteView
):
    """
    Used by the EventFeedback owner to delete their own feedback.
    """

    model = models.EventFeedback
    template_name = "eventfeedback_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Your feedback was deleted")
        return self.event.get_absolute_url()
