import logging
import os
from itertools import chain

from camps.mixins import CampViewMixin
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files import File
from django.db.models import Sum
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from economy.models import Chain, Credebtor, Expense, Reimbursement, Revenue
from facilities.models import FacilityFeedback
from profiles.models import Profile
from program.autoscheduler import AutoScheduler
from program.mixins import AvailabilityMatrixViewMixin
from program.models import (
    Event,
    EventFeedback,
    EventInstance,
    EventLocation,
    EventProposal,
    EventSession,
    EventType,
    Speaker,
    SpeakerProposal,
)
from program.utils import (
    add_matrix_availability,
    get_speaker_availability_form_matrix,
    save_speaker_availability,
)
from psycopg2.extras import DateTimeTZRange
from shop.models import Order, OrderProductRelation
from teams.models import Team
from tickets.models import DiscountTicket, ShopTicket, SponsorTicket, TicketType

from .forms import AutoScheduleApplyForm, AutoScheduleValidateForm, SpeakerForm
from .mixins import (
    ContentTeamPermissionMixin,
    EconomyTeamPermissionMixin,
    InfoTeamPermissionMixin,
    OrgaTeamPermissionMixin,
    RaisePermissionRequiredMixin,
)

logger = logging.getLogger("bornhack.%s" % __name__)


class BackofficeIndexView(CampViewMixin, RaisePermissionRequiredMixin, TemplateView):
    """
    The Backoffice index view only requires camps.backoffice_permission so we use RaisePermissionRequiredMixin directly
    """

    permission_required = "camps.backoffice_permission"
    template_name = "index.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["facilityfeedback_teams"] = Team.objects.filter(
            id__in=set(
                FacilityFeedback.objects.filter(
                    facility__facility_type__responsible_team__camp=self.camp,
                    handled=False,
                ).values_list(
                    "facility__facility_type__responsible_team__id", flat=True
                )
            )
        )
        return context


class FacilityFeedbackView(CampViewMixin, RaisePermissionRequiredMixin, FormView):
    template_name = "facilityfeedback_backoffice.html"

    def get_permission_required(self):
        """
        This view requires two permissions, camps.backoffice_permission and
        the permission_set for the team in question.
        """
        if not self.team.permission_set:
            raise PermissionDenied("No permissions set defined for this team")
        return ["camps.backoffice_permission", self.team.permission_set]

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.team = get_object_or_404(
            Team, camp=self.camp, slug=self.kwargs["team_slug"]
        )
        self.queryset = FacilityFeedback.objects.filter(
            facility__facility_type__responsible_team=self.team, handled=False
        )
        self.form_class = modelformset_factory(
            FacilityFeedback,
            fields=("handled",),
            min_num=self.queryset.count(),
            validate_min=True,
            max_num=self.queryset.count(),
            validate_max=True,
            extra=0,
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["team"] = self.team
        context["feedback_list"] = self.queryset
        context["formset"] = self.form_class(queryset=self.queryset)
        return context

    def form_valid(self, form):
        form.save()
        if form.changed_objects:
            messages.success(
                self.request,
                f"Marked {len(form.changed_objects)} FacilityFeedbacks as handled!",
            )
        return redirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        return reverse(
            "backoffice:facilityfeedback",
            kwargs={"camp_slug": self.camp.slug, "team_slug": self.team.slug},
        )


class ProductHandoutView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    template_name = "product_handout.html"

    def get_queryset(self, **kwargs):
        return OrderProductRelation.objects.filter(
            ticket_generated=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
        ).order_by("order")


class BadgeHandoutView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    template_name = "badge_handout.html"
    context_object_name = "tickets"

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(badge_ticket_generated=False)
        sponsortickets = SponsorTicket.objects.filter(badge_ticket_generated=False)
        discounttickets = DiscountTicket.objects.filter(badge_ticket_generated=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))


class TicketCheckinView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    template_name = "ticket_checkin.html"
    context_object_name = "tickets"

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(used=False)
        sponsortickets = SponsorTicket.objects.filter(used=False)
        discounttickets = DiscountTicket.objects.filter(used=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))


class ApproveNamesView(CampViewMixin, OrgaTeamPermissionMixin, ListView):
    template_name = "approve_public_credit_names.html"
    context_object_name = "profiles"

    def get_queryset(self, **kwargs):
        return Profile.objects.filter(public_credit_name_approved=False).exclude(
            public_credit_name=""
        )


class ApproveFeedbackView(CampViewMixin, ContentTeamPermissionMixin, FormView):
    """
    This view shows a list of EventFeedback objects which are pending approval.
    """

    model = EventFeedback
    template_name = "approve_feedback.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.queryset = EventFeedback.objects.filter(
            event__track__camp=self.camp, approved__isnull=True
        )

        self.form_class = modelformset_factory(
            EventFeedback,
            fields=("approved",),
            min_num=self.queryset.count(),
            validate_min=True,
            max_num=self.queryset.count(),
            validate_max=True,
            extra=0,
        )

    def get_context_data(self, *args, **kwargs):
        """
        Include the queryset used for the modelformset_factory so we have
        some idea which object is which in the template
        Why the hell do the forms in the formset not include the object?
        """
        context = super().get_context_data(*args, **kwargs)
        context["eventfeedback_list"] = self.queryset
        context["formset"] = self.form_class(queryset=self.queryset)
        return context

    def form_valid(self, form):
        form.save()
        if form.changed_objects:
            messages.success(
                self.request, f"Updated {len(form.changed_objects)} EventFeedbacks"
            )
        return redirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        return reverse(
            "backoffice:approve_eventfeedback", kwargs={"camp_slug": self.camp.slug}
        )


#######################################
# MANAGE SPEAKER/EVENT PROPOSAL VIEWS


class ManageProposalsView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """
    This view shows a list of pending SpeakerProposal and EventProposals.
    """

    template_name = "manage_proposals.html"
    context_object_name = "speakerproposals"

    def get_queryset(self, **kwargs):
        return SpeakerProposal.objects.filter(
            camp=self.camp, proposal_status=SpeakerProposal.PROPOSAL_PENDING
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["eventproposals"] = EventProposal.objects.filter(
            track__camp=self.camp, proposal_status=EventProposal.PROPOSAL_PENDING
        )
        return context


class ProposalManageBaseView(CampViewMixin, ContentTeamPermissionMixin, UpdateView):
    """
    This class contains the shared logic between SpeakerProposalManageView and EventProposalManageView
    """

    fields = ["reason"]

    def form_valid(self, form):
        """
        We have two submit buttons in this form, Approve and Reject
        """
        if "approve" in form.data:
            # approve button was pressed
            form.instance.mark_as_approved(self.request)
        elif "reject" in form.data:
            # reject button was pressed
            form.instance.mark_as_rejected(self.request)
        else:
            messages.error(self.request, "Unknown submit action")
        return redirect(
            reverse("backoffice:manage_proposals", kwargs={"camp_slug": self.camp.slug})
        )


class SpeakerProposalManageView(ProposalManageBaseView):
    """
    This view allows an admin to approve/reject SpeakerProposals
    """

    model = SpeakerProposal
    template_name = "manage_speakerproposal.html"

    def setup(self, *args, **kwargs):
        """ Get the speaker availability matrix"""
        super().setup(*args, **kwargs)
        # get the form field matrix for speaker availability
        self.matrix = get_speaker_availability_form_matrix(
            sessions=self.camp.eventsessions.filter(
                event_type__in=EventType.objects.filter(
                    eventproposals__in=self.get_object().eventproposals.all()
                ).distinct()
            )
        )
        add_matrix_availability(self.matrix, self.get_object())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["matrix"] = self.matrix
        return context


class EventProposalManageView(ProposalManageBaseView):
    """
    This view allows an admin to approve/reject EventProposals
    """

    model = EventProposal
    template_name = "manage_eventproposal.html"


################################
# MANAGE SPEAKER VIEWS


class SpeakerListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """ This view is used by the Content Team to see Speaker objects. """

    model = Speaker
    template_name = "speaker_list_backoffice.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("events__instances", "events__event_type")
        return qs


class SpeakerDetailView(
    AvailabilityMatrixViewMixin, ContentTeamPermissionMixin, DetailView
):
    """ This view is used by the Content Team to see details for Speaker objects """

    model = Speaker
    template_name = "speaker_detail_backoffice.html"


class SpeakerUpdateView(
    AvailabilityMatrixViewMixin, ContentTeamPermissionMixin, UpdateView
):
    """ This view is used by the Content Team to update Speaker objects """

    model = Speaker
    template_name = "speaker_update.html"
    form_class = SpeakerForm

    def form_valid(self, form):
        """ Save object and availability """
        speaker = form.save()
        save_speaker_availability(form, obj=speaker)
        messages.success(self.request, "Speaker has been updated")
        return redirect(
            reverse(
                "backoffice:speaker_detail",
                kwargs={"camp_slug": self.camp.slug, "slug": self.get_object().slug},
            )
        )


class SpeakerDeleteView(CampViewMixin, ContentTeamPermissionMixin, DeleteView):
    """ This view is used by the Content Team to delete Speaker objects """

    model = Speaker
    template_name = "speaker_delete.html"

    def delete(self, *args, **kwargs):
        speaker = self.get_object()
        # delete related objects first
        speaker.availabilities.all().delete()
        speaker.urls.all().delete()
        if hasattr(speaker, "eventconflicts"):
            speaker.eventconflicts.delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request, f"Speaker '{self.get_object().name}' has been deleted"
        )
        return reverse("backoffice:speaker_list", kwargs={"camp_slug": self.camp.slug})


################################
# MANAGE EVENT VIEWS


class EventListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """ This view is used by the Content Team to see Event objects. """

    model = Event
    template_name = "event_list_backoffice.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("speakers__events", "event_type", "instances")
        return qs


class EventDetailView(CampViewMixin, ContentTeamPermissionMixin, DetailView):
    """ This view is used by the Content Team to see details for Event objects """

    model = Event
    template_name = "event_detail_backoffice.html"


class EventUpdateView(CampViewMixin, ContentTeamPermissionMixin, UpdateView):
    """ This view is used by the Content Team to update Event objects """

    model = Event
    fields = ["title", "abstract", "video_recording", "duration_minutes", "demand"]
    template_name = "event_update.html"

    def get_success_url(self):
        messages.success(self.request, "Event has been updated")
        return reverse(
            "backoffice:event_detail",
            kwargs={"camp_slug": self.camp.slug, "slug": self.get_object().slug},
        )


class EventDeleteView(CampViewMixin, ContentTeamPermissionMixin, DeleteView):
    """ This view is used by the Content Team to delete Event objects """

    model = Event
    template_name = "event_delete.html"

    def delete(self, *args, **kwargs):
        event = self.get_object()
        self.count, _ = event.instances.all().delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            f"Event '{self.get_object().title}' has been deleted, along with {self.count} EventInstances!",
        )
        return reverse("backoffice:event_list", kwargs={"camp_slug": self.camp.slug})


################################
# MANAGE EVENTINSTANCE VIEWS


class EventInstanceCreateEventSelectView(
    CampViewMixin, ContentTeamPermissionMixin, ListView
):
    """
    This view is shown first when creating a new EventInstance. It shows a
    list of events which can be sorted and filtered and searched, and an
    event can be chosen for the EventInstance creation.
    """

    model = Event
    template_name = "eventinstancecreate_eventselect.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("event_type", "speakers__events", "instances")
        return qs


class EventInstanceCreateView(CampViewMixin, ContentTeamPermissionMixin, CreateView):
    """ This view is used by the Content Team to create EventInstance objects,
    aka. schedule events. It can show a table with radioselect buttons or a freehand
    form where location and start/end time can be written manually, optionally
    skipping speaker availability validation """

    model = EventInstance
    fields = []

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.event = get_object_or_404(Event, pk=kwargs["event_id"])

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related(
            "event", "location", "event__speakers", "event__event_type"
        )
        return qs

    def get_template_names(self):
        if self.kwargs["manual"]:
            return "eventinstance_form_manual.html"
        else:
            return "eventinstance_form_slots.html"

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if self.kwargs["manual"]:
            form.fields["start_time"] = forms.DateTimeField(
                help_text="Start time (format is YYYY-MM-DD HH:MM)"
            )
            form.fields["end_time"] = forms.DateTimeField(
                help_text="End time (format is YYYY-MM-DD HH:MM)"
            )
            form.fields["event_location"] = forms.ChoiceField(
                choices=self.camp.event_locations.all().values_list("id", "name"),
                help_text="The location to schedule the event in",
            )
        else:
            self.slots = []
            slotindex = 0
            # loop over sessions, get free slots, add to list
            for session in self.camp.event_sessions.filter(
                event_type=self.event.event_type
            ):
                for slot in session.get_available_slots():
                    self.slots.append(
                        {"index": slotindex, "session": session, "slot": slot}
                    )
                    slotindex += 1
            form.fields["slot"] = forms.ChoiceField(
                widget=forms.RadioSelect,
                choices=[(s["index"], s["index"]) for s in self.slots],
            )
        form.fields["check_speaker_availabilities"] = forms.BooleanField(
            required=False,
            help_text="Check that speakers are available before saving. Uncheck to bypass validation.",
        )
        return form

    def get_initial(self):
        initial = super().get_initial()
        initial["check_speaker_availabilities"] = True
        return initial

    def get_context_data(self, *args, **kwargs):
        """
        Add event to context
        """
        context = super().get_context_data(*args, **kwargs)
        context["event"] = self.event
        if not self.kwargs["manual"]:
            context["slots"] = self.slots
        return context

    def form_valid(self, form):
        """
        Set needed values, save and return
        """
        if self.kwargs["manual"]:
            when = DateTimeTZRange(
                form.cleaned_data["start_time"], form.cleaned_data["end_time"]
            )
            location = self.camp.event_locations.get(
                id=form.cleaned_data["event_location"]
            )
        else:
            slot = self.slots[int(form.cleaned_data["slot"])]
            when = slot["slot"]
            location = slot["session"].event_location
        eventinstance = form.save(commit=False)
        eventinstance.event = self.event
        eventinstance.location = location
        eventinstance.when = when
        eventinstance.autoscheduled = False

        # validate speakers and location
        try:
            if form.cleaned_data["check_speaker_availabilities"]:
                eventinstance.clean_speakers()
            eventinstance.clean_location()
        except ValidationError as E:
            # add a non-field-specific error since the form fields differ
            form.add_error(None, E)
            return self.form_invalid(form)

        # ok, save and redirect
        eventinstance.save(
            clean_speakers=form.cleaned_data["check_speaker_availabilities"],
        )
        messages.success(
            self.request,
            f"{self.event.title} has been scheduled to begin at {eventinstance.when.lower} at location {eventinstance.location} successfully!",
        )
        return redirect(
            reverse(
                "backoffice:eventinstance_list", kwargs={"camp_slug": self.camp.slug}
            )
        )


class EventInstanceListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """ This view is used by the Content Team to see EventInstance objects. """

    model = EventInstance
    template_name = "eventinstance_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related(
            "event", "location", "event__speakers", "event__event_type"
        )
        return qs


class EventInstanceDetailView(CampViewMixin, ContentTeamPermissionMixin, DetailView):
    """ This view is used by the Content Team to see details for EventInstance objects """

    model = EventInstance
    template_name = "eventinstance_detail.html"


class EventInstanceDeleteView(CampViewMixin, ContentTeamPermissionMixin, DeleteView):
    """ This view is used by the Content Team to delete EventInstance objects """

    model = EventInstance
    template_name = "eventinstance_delete.html"

    def get_success_url(self):
        messages.success(self.request, "EventInstance was deleted successfully!")
        return reverse(
            "backoffice:eventinstance_list", kwargs={"camp_slug": self.camp.slug}
        )


################################
# MANAGE EVENTSESSION VIEWS


class EventSessionCreateTypeSelectView(
    CampViewMixin, ContentTeamPermissionMixin, ListView
):
    """
    This view is shown first when creating a new EventSession
    """

    model = EventType
    template_name = "eventsession_typeselect.html"


class EventSessionCreateLocationSelectView(
    CampViewMixin, ContentTeamPermissionMixin, ListView
):
    """
    This view is shown second when creating a new EventSession
    """

    model = EventLocation
    template_name = "eventsession_locationselect.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.event_type = get_object_or_404(EventType, slug=kwargs["eventtype_slug"])

    def get_context_data(self, *args, **kwargs):
        """
        Add eventtype to context
        """
        context = super().get_context_data(*args, **kwargs)
        context["event_type"] = self.event_type
        return context


class EventSessionFormViewMixin:
    """
    A mixin with the stuff shared between EventSession{Create|Update}View
    """

    def get_form(self, *args, **kwargs):
        """
        The default range widgets are a bit shit because they eat the help_text and
        have no indication of which field is for what. So we add a nice placeholder.
        We also limit the event_location dropdown to only the current camps locations.
        """
        form = super().get_form(*args, **kwargs)
        form.fields["when"].widget.widgets[0].attrs = {
            "placeholder": f"Start Date and Time (YYYY-MM-DD HH:MM). Time zone is {settings.TIME_ZONE}.",
        }
        form.fields["when"].widget.widgets[1].attrs = {
            "placeholder": f"End Date and Time (YYYY-MM-DD HH:MM). Time zone is {settings.TIME_ZONE}.",
        }
        if hasattr(form.fields, "event_location"):
            form.fields["event_location"].queryset = EventLocation.objects.filter(
                camp=self.camp
            )
        return form

    def get_context_data(self, *args, **kwargs):
        """
        Add eventtype and location and existing sessions to context
        """
        context = super().get_context_data(*args, **kwargs)
        if not hasattr(self, "event_type"):
            self.event_type = self.get_object().event_type
        context["event_type"] = self.event_type

        if not hasattr(self, "event_location"):
            self.event_location = self.get_object().event_location
        context["event_location"] = self.event_location

        context["sessions"] = self.event_type.eventsessions.filter(camp=self.camp)
        return context


class EventSessionCreateView(
    CampViewMixin, ContentTeamPermissionMixin, EventSessionFormViewMixin, CreateView
):
    """
    This view is used by the Content Team to create EventSession objects
    """

    model = EventSession
    fields = ["description", "when"]
    template_name = "eventsession_form.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.event_type = get_object_or_404(EventType, slug=kwargs["eventtype_slug"])
        self.event_location = get_object_or_404(
            EventLocation, camp=self.camp, slug=kwargs["eventlocation_slug"]
        )

    def form_valid(self, form):
        """
        Set camp and event_type, check for overlaps and save
        """
        session = form.save(commit=False)
        session.event_type = self.event_type
        session.event_location = self.event_location
        session.camp = self.camp
        # check for overlaps with other sessions
        try:
            session.clean_when()
        except ValidationError as E:
            form.add_error("when", E)
            return self.form_invalid(form)
        # ok, save and redirect
        session.save()
        messages.success(self.request, f"{session} has been created successfully!")
        return redirect(
            reverse(
                "backoffice:eventsession_list", kwargs={"camp_slug": self.camp.slug}
            )
        )


class EventSessionListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """
    This view is used by the Content Team to see EventSession objects.
    """

    model = EventSession
    template_name = "eventsession_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("event_type", "event_location")
        return qs


class EventSessionDetailView(CampViewMixin, ContentTeamPermissionMixin, DetailView):
    """
    This view is used by the Content Team to see details for EventSession objects
    """

    model = EventSession
    template_name = "eventsession_detail.html"
    context_object_name = "session"


class EventSessionUpdateView(
    CampViewMixin, ContentTeamPermissionMixin, EventSessionFormViewMixin, UpdateView
):
    """
    This view is used by the Content Team to update EventSession objects
    """

    model = EventSession
    fields = ["when", "description"]
    template_name = "eventsession_form.html"

    def setup(self, *args, **kwargs):
        """ Show a warning if we have existing EventInstance objects in this session """
        super().setup(*args, **kwargs)
        if self.get_object().eventinstances.exists():
            messages.warning(
                self.request,
                "NOTE: One or more EventInstances exists (partially or fully) inside this EventSession. Make sure you are updating the correct session!",
            )

    def form_valid(self, form):
        """
        Check for overlaps and save
        """
        session = form.save(commit=False)
        # check for overlaps with other sessions
        try:
            session.clean_when()
        except ValidationError as E:
            form.add_error("when", E)
            return self.form_invalid(form)
        # ok, save and redirect
        session.save()
        messages.success(self.request, f"{session} has been updated successfully!")
        return redirect(
            reverse(
                "backoffice:eventsession_list", kwargs={"camp_slug": self.camp.slug}
            )
        )


class EventSessionDeleteView(CampViewMixin, ContentTeamPermissionMixin, DeleteView):
    """
    This view is used by the Content Team to delete EventSession objects
    """

    model = EventSession
    template_name = "eventsession_delete.html"
    context_object_name = "session"

    def get(self, *args, **kwargs):
        """ Show a warning if we have existing EventInstance objects in this session """
        if self.get_object().eventinstances.exists():
            messages.warning(
                self.request,
                "NOTE: One or more EventInstances exists (partially or fully) inside this EventSession. Make sure you are deleting the correct session!",
            )
        return super().get(*args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "EventSession was deleted successfully!")
        return reverse(
            "backoffice:eventsession_list", kwargs={"camp_slug": self.camp.slug}
        )


################################
# AUTOSCHEDULER VIEWS


class AutoScheduleManageView(CampViewMixin, ContentTeamPermissionMixin, TemplateView):
    """ Just an index type view with links to the various actions """

    template_name = "autoschedule_index.html"


class AutoScheduleCrashCourseView(
    CampViewMixin, ContentTeamPermissionMixin, TemplateView
):
    """ A short crash course on the autoscheduler """

    template_name = "autoschedule_crash_course.html"


class AutoScheduleValidateView(CampViewMixin, ContentTeamPermissionMixin, FormView):
    """ This view is used to validate schedules. It uses the AutoScheduler and can
    either validate the currently applied schedule (existing EventInstances), or a
    new similar schedule, or a brand new schedule """

    template_name = "autoschedule_validate.html"
    form_class = AutoScheduleValidateForm

    def form_valid(self, form):
        # initialise AutoScheduler
        scheduler = AutoScheduler(camp=self.camp)

        # get autoschedule
        if form.cleaned_data["schedule"] == "current":
            autoschedule = scheduler.build_current_autoschedule()
            message = f"The currently scheduled EventInstances form a valid schedule! AutoScheduler has {len(scheduler.autoslots)} Slots based on {scheduler.event_sessions.count()} EventSessions for {scheduler.event_types.count()} EventTypes. {scheduler.events.count()} Events in the schedule."
        elif form.cleaned_data["schedule"] == "similar":
            original_autoschedule = scheduler.build_current_autoschedule()
            autoschedule, diff = scheduler.calculate_similar_autoschedule(
                original_autoschedule
            )
            message = f"The new similar schedule is valid! AutoScheduler has {len(scheduler.autoslots)} Slots based on {scheduler.event_sessions.count()} EventSessions for {scheduler.event_types.count()} EventTypes. Differences to the current schedule: {len(diff['event_diffs'])} Event diffs and {len(diff['slot_diffs'])} Slot diffs."
        elif form.cleaned_data["schedule"] == "new":
            autoschedule = scheduler.calculate_autoschedule()
            message = f"The new schedule is valid! AutoScheduler has {len(scheduler.autoslots)} Slots based on {scheduler.event_sessions.count()} EventSessions for {scheduler.event_types.count()} EventTypes. {scheduler.events.count()} Events in the schedule."

        # check validity
        valid, violations = scheduler.is_valid(autoschedule, return_violations=True)
        if valid:
            messages.success(self.request, message)
        else:
            messages.error(self.request, "Schedule is NOT valid!")
            message = "Schedule violations:<br>"
            for v in violations:
                message += v + "<br>"
            messages.error(self.request, mark_safe(message))
        return redirect(
            reverse(
                "backoffice:autoschedule_validate", kwargs={"camp_slug": self.camp.slug}
            )
        )


class AutoScheduleDiffView(CampViewMixin, ContentTeamPermissionMixin, TemplateView):
    template_name = "autoschedule_diff.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        scheduler = AutoScheduler(camp=self.camp)
        autoschedule, diff = scheduler.calculate_similar_autoschedule()
        context["diff"] = diff
        context["scheduler"] = scheduler
        return context


class AutoScheduleApplyView(CampViewMixin, ContentTeamPermissionMixin, FormView):
    """ This view is used by the Content Team to apply a new schedules by deleting
    all autoscheduled EventInstances, and creating new EventInstance objects for
    each Event/Slot combination in the schedule.

    TODO: see comment in program.autoscheduler.AutoScheduler.apply() method.
    """

    template_name = "autoschedule_apply.html"
    form_class = AutoScheduleApplyForm

    def form_valid(self, form):
        # initialise AutoScheduler
        scheduler = AutoScheduler(camp=self.camp)

        # get autoschedule
        if form.cleaned_data["schedule"] == "similar":
            autoschedule, diff = scheduler.calculate_similar_autoschedule()
        elif form.cleaned_data["schedule"] == "new":
            autoschedule = scheduler.calculate_autoschedule()

        # check validity
        valid, violations = scheduler.is_valid(autoschedule, return_violations=True)
        if valid:
            # schedule is valid, apply it
            deleted, created = scheduler.apply(autoschedule)
            messages.success(
                self.request,
                f"Schedule has been applied! Deleted {deleted} EventInstances and created {created} new EventInstances. Differences to the previous schedule: {len(diff['event_diffs'])} Event diffs and {len(diff['slot_diffs'])} Slot diffs.",
            )
        else:
            messages.error(self.request, "Schedule is NOT valid, cannot apply!")
        return redirect(
            reverse(
                "backoffice:autoschedule_apply", kwargs={"camp_slug": self.camp.slug}
            )
        )


class AutoScheduleDebugEventSlotUnavailabilityView(
    CampViewMixin, ContentTeamPermissionMixin, TemplateView
):
    template_name = "autoschedule_debug_slots.html"

    def get_context_data(self, **kwargs):
        scheduler = AutoScheduler(camp=self.camp)
        context = {
            "scheduler": scheduler,
        }
        return context


class AutoScheduleDebugEventConflictsView(
    CampViewMixin, ContentTeamPermissionMixin, TemplateView
):
    template_name = "autoschedule_debug_events.html"

    def get_context_data(self, **kwargs):
        scheduler = AutoScheduler(camp=self.camp)
        context = {
            "scheduler": scheduler,
        }
        return context


################################
# MERCHANDISE VIEWS


class MerchandiseOrdersView(CampViewMixin, OrgaTeamPermissionMixin, ListView):
    template_name = "orders_merchandise.html"

    def get_queryset(self, **kwargs):
        camp_prefix = "BornHack {}".format(timezone.now().year)

        return (
            OrderProductRelation.objects.filter(
                ticket_generated=False,
                order__paid=True,
                order__refunded=False,
                order__cancelled=False,
                product__category__name="Merchandise",
            )
            .filter(product__name__startswith=camp_prefix)
            .order_by("order")
        )


class MerchandiseToOrderView(CampViewMixin, OrgaTeamPermissionMixin, TemplateView):
    template_name = "merchandise_to_order.html"

    def get_context_data(self, **kwargs):
        camp_prefix = "BornHack {}".format(timezone.now().year)

        order_relations = OrderProductRelation.objects.filter(
            ticket_generated=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
            product__category__name="Merchandise",
        ).filter(product__name__startswith=camp_prefix)

        merchandise_orders = {}
        for relation in order_relations:
            try:
                quantity = merchandise_orders[relation.product.name] + relation.quantity
                merchandise_orders[relation.product.name] = quantity
            except KeyError:
                merchandise_orders[relation.product.name] = relation.quantity

        context = super().get_context_data(**kwargs)
        context["merchandise"] = merchandise_orders
        return context


################################
# VILLAGE VIEWS


class VillageOrdersView(CampViewMixin, OrgaTeamPermissionMixin, ListView):
    template_name = "orders_village.html"

    def get_queryset(self, **kwargs):
        camp_prefix = "BornHack {}".format(timezone.now().year)

        return (
            OrderProductRelation.objects.filter(
                ticket_generated=False,
                order__paid=True,
                order__refunded=False,
                order__cancelled=False,
                product__category__name="Villages",
            )
            .filter(product__name__startswith=camp_prefix)
            .order_by("order")
        )


class VillageToOrderView(CampViewMixin, OrgaTeamPermissionMixin, TemplateView):
    template_name = "village_to_order.html"

    def get_context_data(self, **kwargs):
        camp_prefix = "BornHack {}".format(timezone.now().year)

        order_relations = OrderProductRelation.objects.filter(
            ticket_generated=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
            product__category__name="Villages",
        ).filter(product__name__startswith=camp_prefix)

        village_orders = {}
        for relation in order_relations:
            try:
                quantity = village_orders[relation.product.name] + relation.quantity
                village_orders[relation.product.name] = quantity
            except KeyError:
                village_orders[relation.product.name] = relation.quantity

        context = super().get_context_data(**kwargs)
        context["village"] = village_orders
        return context


################################
# CHAINS & CREDEBTORS


class ChainListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Chain
    template_name = "chain_list_backoffice.html"


class ChainDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Chain
    template_name = "chain_detail_backoffice.html"
    slug_url_kwarg = "chain_slug"


class CredebtorDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Credebtor
    template_name = "credebtor_detail_backoffice.html"
    slug_url_kwarg = "credebtor_slug"


################################
# EXPENSES


class ExpenseListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Expense
    template_name = "expense_list_backoffice.html"

    def get_queryset(self, **kwargs):
        """
        Exclude unapproved expenses, they are shown seperately
        """
        queryset = super().get_queryset(**kwargs)
        return queryset.exclude(approved__isnull=True)

    def get_context_data(self, **kwargs):
        """
        Include unapproved expenses seperately
        """
        context = super().get_context_data(**kwargs)
        context["unapproved_expenses"] = Expense.objects.filter(
            camp=self.camp, approved__isnull=True
        )
        return context


class ExpenseDetailView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Expense
    template_name = "expense_detail_backoffice.html"
    fields = ["notes"]

    def form_valid(self, form):
        """
        We have two submit buttons in this form, Approve and Reject
        """
        expense = form.save()
        if "approve" in form.data:
            # approve button was pressed
            expense.approve(self.request)
        elif "reject" in form.data:
            # reject button was pressed
            expense.reject(self.request)
        else:
            messages.error(self.request, "Unknown submit action")
        return redirect(
            reverse("backoffice:expense_list", kwargs={"camp_slug": self.camp.slug})
        )


######################################
# REIMBURSEMENTS


class ReimbursementListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Reimbursement
    template_name = "reimbursement_list_backoffice.html"


class ReimbursementDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Reimbursement
    template_name = "reimbursement_detail_backoffice.html"


class ReimbursementCreateUserSelectView(
    CampViewMixin, EconomyTeamPermissionMixin, ListView
):
    template_name = "reimbursement_create_userselect.html"

    def get_queryset(self):
        queryset = User.objects.filter(
            id__in=Expense.objects.filter(
                camp=self.camp,
                reimbursement__isnull=True,
                paid_by_bornhack=False,
                approved=True,
            )
            .values_list("user", flat=True)
            .distinct()
        )
        return queryset


class ReimbursementCreateView(CampViewMixin, EconomyTeamPermissionMixin, CreateView):
    model = Reimbursement
    template_name = "reimbursement_create.html"
    fields = ["notes", "paid"]

    def dispatch(self, request, *args, **kwargs):
        """ Get the user from kwargs """
        self.reimbursement_user = get_object_or_404(User, pk=kwargs["user_id"])

        # get response now so we have self.camp available below
        response = super().dispatch(request, *args, **kwargs)

        # return the response
        return response

    def get(self, request, *args, **kwargs):
        # does this user have any approved and un-reimbursed expenses?
        if not self.reimbursement_user.expenses.filter(
            reimbursement__isnull=True, approved=True, paid_by_bornhack=False
        ):
            messages.error(
                request, "This user has no approved and unreimbursed expenses!"
            )
            return redirect(
                reverse("backoffice:index", kwargs={"camp_slug": self.camp.slug})
            )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expenses"] = Expense.objects.filter(
            user=self.reimbursement_user,
            approved=True,
            reimbursement__isnull=True,
            paid_by_bornhack=False,
        )
        context["total_amount"] = context["expenses"].aggregate(Sum("amount"))
        context["reimbursement_user"] = self.reimbursement_user
        return context

    def form_valid(self, form):
        """
        Set user and camp for the Reimbursement before saving
        """
        # get the expenses for this user
        expenses = Expense.objects.filter(
            user=self.reimbursement_user,
            approved=True,
            reimbursement__isnull=True,
            paid_by_bornhack=False,
        )
        if not expenses:
            messages.error(self.request, "No expenses found")
            return redirect(
                reverse(
                    "backoffice:reimbursement_list",
                    kwargs={"camp_slug": self.camp.slug},
                )
            )

        # get the Economy team for this camp
        try:
            economyteam = Team.objects.get(
                camp=self.camp, name=settings.ECONOMYTEAM_NAME
            )
        except Team.DoesNotExist:
            messages.error(self.request, "No economy team found")
            return redirect(
                reverse(
                    "backoffice:reimbursement_list",
                    kwargs={"camp_slug": self.camp.slug},
                )
            )

        # create reimbursement in database
        reimbursement = form.save(commit=False)
        reimbursement.reimbursement_user = self.reimbursement_user
        reimbursement.user = self.request.user
        reimbursement.camp = self.camp
        reimbursement.save()

        # add all expenses to reimbursement
        for expense in expenses:
            expense.reimbursement = reimbursement
            expense.save()

        # create expense for this reimbursement
        expense = Expense()
        expense.camp = self.camp
        expense.user = self.request.user
        expense.amount = reimbursement.amount
        expense.description = "Payment of reimbursement %s to %s" % (
            reimbursement.pk,
            reimbursement.reimbursement_user,
        )
        expense.paid_by_bornhack = True
        expense.responsible_team = economyteam
        expense.approved = True
        expense.reimbursement = reimbursement
        expense.invoice_date = timezone.now()
        expense.creditor = Credebtor.objects.get(name="Reimbursement")
        expense.invoice.save(
            "na.jpg",
            File(
                open(
                    os.path.join(settings.DJANGO_BASE_PATH, "static_src/img/na.jpg"),
                    "rb",
                )
            ),
        )
        expense.save()

        messages.success(
            self.request,
            "Reimbursement %s has been created with invoice_date %s"
            % (reimbursement.pk, timezone.now()),
        )
        return redirect(
            reverse(
                "backoffice:reimbursement_detail",
                kwargs={"camp_slug": self.camp.slug, "pk": reimbursement.pk},
            )
        )


class ReimbursementUpdateView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Reimbursement
    template_name = "reimbursement_form.html"
    fields = ["notes", "paid"]

    def get_success_url(self):
        return reverse(
            "backoffice:reimbursement_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.get_object().pk},
        )


class ReimbursementDeleteView(CampViewMixin, EconomyTeamPermissionMixin, DeleteView):
    model = Reimbursement
    template_name = "reimbursement_delete.html"
    fields = ["notes", "paid"]

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.get_object().paid:
            messages.error(
                request,
                "This reimbursement has already been paid so it cannot be deleted",
            )
            return redirect(
                reverse(
                    "backoffice:reimbursement_list",
                    kwargs={"camp_slug": self.camp.slug},
                )
            )
        return response


################################
# REVENUES


class RevenueListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Revenue
    template_name = "revenue_list_backoffice.html"

    def get_queryset(self, **kwargs):
        """
        Exclude unapproved revenues, they are shown seperately
        """
        queryset = super().get_queryset(**kwargs)
        return queryset.exclude(approved__isnull=True)

    def get_context_data(self, **kwargs):
        """
        Include unapproved revenues seperately
        """
        context = super().get_context_data(**kwargs)
        context["unapproved_revenues"] = Revenue.objects.filter(
            camp=self.camp, approved__isnull=True
        )
        return context


class RevenueDetailView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Revenue
    template_name = "revenue_detail_backoffice.html"
    fields = ["notes"]

    def form_valid(self, form):
        """
        We have two submit buttons in this form, Approve and Reject
        """
        revenue = form.save()
        if "approve" in form.data:
            # approve button was pressed
            revenue.approve(self.request)
        elif "reject" in form.data:
            # reject button was pressed
            revenue.reject(self.request)
        else:
            messages.error(self.request, "Unknown submit action")
        return redirect(
            reverse("backoffice:revenue_list", kwargs={"camp_slug": self.camp.slug})
        )


def _ticket_getter_by_token(token):
    for ticket_class in [ShopTicket, SponsorTicket, DiscountTicket]:
        try:
            return ticket_class.objects.get(token=token), False
        except ticket_class.DoesNotExist:
            try:
                return ticket_class.objects.get(badge_token=token), True
            except ticket_class.DoesNotExist:
                pass


def _ticket_getter_by_pk(pk):
    for ticket_class in [ShopTicket, SponsorTicket, DiscountTicket]:
        try:
            return ticket_class.objects.get(pk=pk)
        except ticket_class.DoesNotExist:
            pass


class ScanTicketsView(
    LoginRequiredMixin, InfoTeamPermissionMixin, CampViewMixin, TemplateView
):
    template_name = "info_desk/scan.html"

    ticket = None
    order = None
    order_search = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.ticket:
            context["ticket"] = self.ticket

        elif "ticket_token" in self.request.POST:

            # Slice to get rid of the first character which is a '#'
            ticket_token = self.request.POST.get("ticket_token")[1:]

            ticket, is_badge = _ticket_getter_by_token(ticket_token)

            if ticket:
                context["ticket"] = ticket
                context["is_badge"] = is_badge
            else:
                messages.warning(self.request, "Ticket not found!")

        elif self.order_search:
            context["order"] = self.order

        return context

    def post(self, request, **kwargs):
        if "check_in_ticket_id" in request.POST:
            self.ticket = self.check_in_ticket(request)
        elif "badge_ticket_id" in request.POST:
            self.ticket = self.hand_out_badge(request)
        elif "find_order_id" in request.POST:
            self.order_search = True
            try:
                order_id = self.request.POST.get("find_order_id")
                self.order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                pass
        elif "mark_as_paid" in request.POST:
            self.mark_order_as_paid(request)

        return super().get(request, **kwargs)

    def check_in_ticket(self, request):
        check_in_ticket_id = request.POST.get("check_in_ticket_id")
        ticket_to_check_in = _ticket_getter_by_pk(check_in_ticket_id)
        ticket_to_check_in.used = True
        ticket_to_check_in.save()
        messages.info(request, "Ticket checked-in!")
        return ticket_to_check_in

    def hand_out_badge(self, request):
        badge_ticket_id = request.POST.get("badge_ticket_id")
        ticket_to_handout_badge_for = _ticket_getter_by_pk(badge_ticket_id)
        ticket_to_handout_badge_for.badge_handed_out = True
        ticket_to_handout_badge_for.save()
        messages.info(request, "Badge marked as handed out!")
        return ticket_to_handout_badge_for

    def mark_order_as_paid(self, request):
        order = Order.objects.get(id=request.POST.get("mark_as_paid"))
        order.mark_as_paid()
        messages.success(request, "Order #{} has been marked as paid!".format(order.id))


class ShopTicketOverview(LoginRequiredMixin, CampViewMixin, ListView):

    model = ShopTicket

    template_name = "shop_ticket_overview.html"

    context_object_name = "shop_tickets"

    def get_context_data(self, *, object_list=None, **kwargs):
        kwargs["ticket_types"] = TicketType.objects.filter(camp=self.camp)
        return super().get_context_data(object_list=object_list, **kwargs)
