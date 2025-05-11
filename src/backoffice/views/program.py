import copy
import logging

from django import forms
from django.conf import settings
from django.contrib import messages
from django.db.models import Count
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView

from camps.mixins import CampViewMixin
from program.autoscheduler import AutoScheduler
from program.email import add_event_scheduled_email
from program.mixins import AvailabilityMatrixViewMixin
from program.models import Event
from program.models import EventLocation
from program.models import EventProposal
from program.models import EventSession
from program.models import EventSlot
from program.models import EventType
from program.models import Speaker
from program.models import SpeakerProposal
from program.utils import save_speaker_availability

from ..forms import AutoScheduleApplyForm
from ..forms import AutoScheduleValidateForm
from ..forms import EventScheduleForm
from ..forms import SpeakerForm
from ..mixins import ContentTeamPermissionMixin

logger = logging.getLogger("bornhack.%s" % __name__)


#######################################
# MANAGE SPEAKER/EVENT PROPOSAL VIEWS


class PendingProposalsView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """This convenience view shows a list of pending proposals"""

    model = SpeakerProposal
    template_name = "pending_proposals.html"
    context_object_name = "speaker_proposal_list"

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs).filter(proposal_status="pending")
        qs = qs.prefetch_related("user", "urls", "speaker")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event_proposal_list"] = self.camp.event_proposals.filter(
            proposal_status=EventProposal.PROPOSAL_PENDING,
        ).prefetch_related("event_type", "track", "speakers", "tags", "user", "event")
        return context


class ProposalApproveBaseView(CampViewMixin, ContentTeamPermissionMixin, UpdateView):
    """Shared logic between SpeakerProposalApproveView and EventProposalApproveView"""

    fields = ["reason"]

    def form_valid(self, form):
        """We have two submit buttons in this form, Approve and Reject"""
        if "approve" in form.data:
            # approve button was pressed
            form.instance.mark_as_approved(self.request)
        elif "reject" in form.data:
            # reject button was pressed
            form.instance.mark_as_rejected(self.request)
        else:
            messages.error(self.request, "Unknown submit action")
        return redirect(
            reverse(
                "backoffice:pending_proposals",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


class SpeakerProposalListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """This view permits Content Team members to list SpeakerProposals"""

    model = SpeakerProposal
    template_name = "speaker_proposal_list.html"
    context_object_name = "speaker_proposal_list"

    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        qs = qs.prefetch_related("user", "urls", "speaker")
        return qs


class SpeakerProposalDetailView(
    AvailabilityMatrixViewMixin,
    ContentTeamPermissionMixin,
    DetailView,
):
    """This view permits Content Team members to see SpeakerProposal details"""

    model = SpeakerProposal
    template_name = "speaker_proposal_detail_backoffice.html"
    context_object_name = "speaker_proposal"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("user", "urls")
        return qs


class SpeakerProposalApproveRejectView(ProposalApproveBaseView):
    """This view allows ContentTeam members to approve/reject SpeakerProposals"""

    model = SpeakerProposal
    template_name = "speaker_proposal_approve_reject.html"
    context_object_name = "speaker_proposal"


class EventProposalListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """This view permits Content Team members to list EventProposals"""

    model = EventProposal
    template_name = "event_proposal_list.html"
    context_object_name = "event_proposal_list"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related(
            "user",
            "urls",
            "event",
            "event_type",
            "speakers__event_proposals",
            "track",
            "tags",
        )
        return qs


class EventProposalDetailView(CampViewMixin, ContentTeamPermissionMixin, DetailView):
    """This view permits Content Team members to see EventProposal details"""

    model = EventProposal
    template_name = "event_proposal_detail_backoffice.html"
    context_object_name = "event_proposal"


class EventProposalApproveRejectView(ProposalApproveBaseView):
    """This view allows ContentTeam members to approve/reject EventProposals"""

    model = EventProposal
    template_name = "event_proposal_approve_reject.html"
    context_object_name = "event_proposal"


################################
# MANAGE SPEAKER VIEWS


class SpeakerListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """This view is used by the Content Team to see Speaker objects."""

    model = Speaker
    template_name = "speaker_list_backoffice.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related(
            "proposal__user",
            "events__event_slots",
            "events__event_type",
            "event_conflicts",
        )
        return qs


class SpeakerDetailView(
    AvailabilityMatrixViewMixin,
    ContentTeamPermissionMixin,
    DetailView,
):
    """This view is used by the Content Team to see details for Speaker objects"""

    model = Speaker
    template_name = "speaker_detail_backoffice.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related(
            "event_conflicts",
            "events__event_slots",
            "events__event_type",
        )
        return qs


class SpeakerUpdateView(
    AvailabilityMatrixViewMixin,
    ContentTeamPermissionMixin,
    UpdateView,
):
    """This view is used by the Content Team to update Speaker objects"""

    model = Speaker
    template_name = "speaker_update.html"
    form_class = SpeakerForm

    def get_form_kwargs(self):
        """Set camp for the form"""
        kwargs = super().get_form_kwargs()
        kwargs.update({"camp": self.camp})
        return kwargs

    def form_valid(self, form):
        """Save object and availability"""
        speaker = form.save()
        save_speaker_availability(form, obj=speaker)
        messages.success(self.request, "Speaker has been updated")
        return redirect(
            reverse(
                "backoffice:speaker_detail",
                kwargs={"camp_slug": self.camp.slug, "slug": self.get_object().slug},
            ),
        )


class SpeakerDeleteView(CampViewMixin, ContentTeamPermissionMixin, DeleteView):
    """This view is used by the Content Team to delete Speaker objects"""

    model = Speaker
    template_name = "speaker_delete.html"

    def delete(self, *args, **kwargs):
        speaker = self.get_object()
        # delete related objects first
        speaker.availabilities.all().delete()
        speaker.urls.all().delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            f"Speaker '{self.get_object().name}' has been deleted",
        )
        return reverse("backoffice:speaker_list", kwargs={"camp_slug": self.camp.slug})


################################
# MANAGE EVENTTYPE VIEWS


class EventTypeListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """This view is used by the Content Team to list EventTypes"""

    model = EventType
    template_name = "event_type_list.html"
    context_object_name = "event_type_list"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.annotate(
            # only count events for the current camp
            event_count=Count(
                "events",
                distinct=True,
                filter=Q(events__track__camp=self.camp),
            ),
            # only count EventSessions for the current camp
            event_sessions_count=Count(
                "event_sessions",
                distinct=True,
                filter=Q(event_sessions__camp=self.camp),
            ),
            # only count EventSlots for the current camp
            event_slots_count=Count(
                "event_sessions__event_slots",
                distinct=True,
                filter=Q(event_sessions__camp=self.camp),
            ),
        )
        return qs


class EventTypeDetailView(CampViewMixin, ContentTeamPermissionMixin, DetailView):
    """This view is used by the Content Team to see details for EventTypes"""

    model = EventType
    template_name = "event_type_detail.html"
    context_object_name = "event_type"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["event_sessions"] = self.camp.event_sessions.filter(
            event_type=self.get_object(),
        ).prefetch_related("event_location", "event_slots")
        context["events"] = self.camp.events.filter(
            event_type=self.get_object(),
        ).prefetch_related(
            "speakers",
            "event_slots__event_session__event_location",
            "event_type",
        )
        return context


################################
# MANAGE EVENTLOCATION VIEWS


class EventLocationListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """This view is used by the Content Team to list EventLocation objects."""

    model = EventLocation
    template_name = "event_location_list.html"
    context_object_name = "event_location_list"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("event_sessions__event_slots", "conflicts")
        return qs


class EventLocationDetailView(CampViewMixin, ContentTeamPermissionMixin, DetailView):
    """This view is used by the Content Team to see details for EventLocation objects"""

    model = EventLocation
    template_name = "event_location_detail.html"
    context_object_name = "event_location"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related(
            "conflicts",
            "event_sessions__event_slots",
            "event_sessions__event_type",
        )
        return qs


class EventLocationCreateView(CampViewMixin, ContentTeamPermissionMixin, CreateView):
    """This view is used by the Content Team to create EventLocation objects"""

    model = EventLocation
    fields = ["name", "icon", "capacity", "conflicts"]
    template_name = "event_location_form.html"

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["conflicts"].queryset = self.camp.event_locations.all()
        return form

    def form_valid(self, form):
        location = form.save(commit=False)
        location.camp = self.camp
        location.save()
        form.save_m2m()
        messages.success(
            self.request,
            f"EventLocation {location.name} has been created",
        )
        return redirect(
            reverse(
                "backoffice:event_location_detail",
                kwargs={"camp_slug": self.camp.slug, "slug": location.slug},
            ),
        )


class EventLocationUpdateView(CampViewMixin, ContentTeamPermissionMixin, UpdateView):
    """This view is used by the Content Team to update EventLocation objects"""

    model = EventLocation
    fields = ["name", "icon", "capacity", "conflicts"]
    template_name = "event_location_form.html"

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["conflicts"].queryset = self.camp.event_locations.exclude(
            pk=self.get_object().pk,
        )
        return form

    def get_success_url(self):
        messages.success(
            self.request,
            f"EventLocation {self.get_object().name} has been updated",
        )
        return reverse(
            "backoffice:event_location_detail",
            kwargs={"camp_slug": self.camp.slug, "slug": self.get_object().slug},
        )


class EventLocationDeleteView(CampViewMixin, ContentTeamPermissionMixin, DeleteView):
    """This view is used by the Content Team to delete EventLocation objects"""

    model = EventLocation
    template_name = "event_location_delete.html"
    context_object_name = "event_location"

    def delete(self, *args, **kwargs):
        slotsdeleted, slotdetails = self.get_object().event_slots.all().delete()
        sessionsdeleted, sessiondetails = self.get_object().event_sessions.all().delete()

        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            f"EventLocation '{self.get_object().name}' has been deleted.",
        )
        return reverse(
            "backoffice:event_location_list",
            kwargs={"camp_slug": self.camp.slug},
        )


################################
# MANAGE EVENT VIEWS


class EventListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """This view is used by the Content Team to see Event objects."""

    model = Event
    template_name = "event_list_backoffice.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related(
            "speakers__events",
            "event_type",
            "event_slots__event_session__event_location",
            "tags",
        )
        return qs


class EventDetailView(CampViewMixin, ContentTeamPermissionMixin, DetailView):
    """This view is used by the Content Team to see details for Event objects"""

    model = Event
    template_name = "event_detail_backoffice.html"


class EventUpdateView(CampViewMixin, ContentTeamPermissionMixin, UpdateView):
    """This view is used by the Content Team to update Event objects"""

    model = Event
    fields = [
        "title",
        "abstract",
        "video_recording",
        "duration_minutes",
        "demand",
        "tags",
    ]
    template_name = "event_update.html"

    def get_success_url(self):
        messages.success(self.request, "Event has been updated")
        return reverse(
            "backoffice:event_detail",
            kwargs={"camp_slug": self.camp.slug, "slug": self.get_object().slug},
        )


class EventDeleteView(CampViewMixin, ContentTeamPermissionMixin, DeleteView):
    """This view is used by the Content Team to delete Event objects"""

    model = Event
    template_name = "event_delete.html"

    def delete(self, *args, **kwargs):
        self.get_object().urls.all().delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            f"Event '{self.get_object().title}' has been deleted!",
        )
        return reverse("backoffice:event_list", kwargs={"camp_slug": self.camp.slug})


class EventScheduleView(CampViewMixin, ContentTeamPermissionMixin, FormView):
    """This view is used by the Content Team to manually schedule Events.
    It shows a table with radioselect buttons for the available slots for the
    EventType of the Event
    """

    form_class = EventScheduleForm
    template_name = "event_schedule.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.event = get_object_or_404(
            Event,
            track__camp=self.camp,
            slug=kwargs["slug"],
        )

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        self.slots = []
        slotindex = 0
        # loop over sessions, get free slots
        for session in self.camp.event_sessions.filter(
            event_type=self.event.event_type,
            event_duration_minutes__gte=self.event.duration_minutes,
        ):
            for slot in session.get_available_slots():
                # loop over speakers to see if they are all available
                for speaker in self.event.speakers.all():
                    if not speaker.is_available(slot.when):
                        # this speaker is not available, skip this slot
                        break
                else:
                    # all speakers are available for this slot
                    self.slots.append({"index": slotindex, "slot": slot})
                    slotindex += 1
        # add the slot choicefield
        form.fields["slot"] = forms.ChoiceField(
            widget=forms.RadioSelect,
            choices=[(s["index"], s["index"]) for s in self.slots],
        )
        return form

    def get_context_data(self, *args, **kwargs):
        """Add event to context"""
        context = super().get_context_data(*args, **kwargs)
        context["event"] = self.event
        context["event_slots"] = self.slots
        return context

    def form_valid(self, form):
        """Set needed values, save slot and return"""
        slot = self.slots[int(form.cleaned_data["slot"])]["slot"]
        slot.event = self.event
        slot.autoscheduled = False
        slot.save()
        messages.success(
            self.request,
            f"{self.event.title} has been scheduled to begin at {slot.when.lower} at location {slot.event_location.name} successfully!",
        )
        add_event_scheduled_email(slot)
        return redirect(
            reverse(
                "backoffice:event_detail",
                kwargs={"camp_slug": self.camp.slug, "slug": self.event.slug},
            ),
        )


################################
# MANAGE EVENTSESSION VIEWS


class EventSessionCreateTypeSelectView(
    CampViewMixin,
    ContentTeamPermissionMixin,
    ListView,
):
    """This view is shown first when creating a new EventSession"""

    model = EventType
    template_name = "event_session_create_type_select.html"
    context_object_name = "event_type_list"


class EventSessionCreateLocationSelectView(
    CampViewMixin,
    ContentTeamPermissionMixin,
    ListView,
):
    """This view is shown second when creating a new EventSession"""

    model = EventLocation
    template_name = "event_session_create_location_select.html"
    context_object_name = "event_location_list"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.event_type = get_object_or_404(EventType, slug=kwargs["event_type_slug"])

    def get_context_data(self, *args, **kwargs):
        """Add event_type to context"""
        context = super().get_context_data(*args, **kwargs)
        context["event_type"] = self.event_type
        return context


class EventSessionFormViewMixin:
    """A mixin with the stuff shared between EventSession{Create|Update}View"""

    def get_form(self, *args, **kwargs):
        """The default range widgets are a bit shit because they eat the help_text and
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
                camp=self.camp,
            )
        return form

    def get_context_data(self, *args, **kwargs):
        """Add event_type and location and existing sessions to context"""
        context = super().get_context_data(*args, **kwargs)
        if not hasattr(self, "event_type"):
            self.event_type = self.get_object().event_type
        context["event_type"] = self.event_type

        if not hasattr(self, "event_location"):
            self.event_location = self.get_object().event_location
        context["event_location"] = self.event_location

        context["sessions"] = self.event_type.event_sessions.filter(camp=self.camp)
        return context


class EventSessionCreateView(
    CampViewMixin,
    ContentTeamPermissionMixin,
    EventSessionFormViewMixin,
    CreateView,
):
    """This view is used by the Content Team to create EventSession objects"""

    model = EventSession
    fields = ["description", "when", "event_duration_minutes"]
    template_name = "event_session_form.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.event_type = get_object_or_404(EventType, slug=kwargs["event_type_slug"])
        self.event_location = get_object_or_404(
            EventLocation,
            camp=self.camp,
            slug=kwargs["event_location_slug"],
        )

    def form_valid(self, form):
        """Set camp and event_type, check for overlaps and save"""
        session = form.save(commit=False)
        session.event_type = self.event_type
        session.event_location = self.event_location
        session.camp = self.camp
        session.save()
        messages.success(self.request, f"{session} has been created successfully!")
        return redirect(
            reverse(
                "backoffice:event_session_list",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


class EventSessionListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """This view is used by the Content Team to see EventSession objects."""

    model = EventSession
    template_name = "event_session_list.html"
    context_object_name = "event_session_list"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related("event_type", "event_location", "event_slots")
        return qs


class EventSessionDetailView(CampViewMixin, ContentTeamPermissionMixin, DetailView):
    """This view is used by the Content Team to see details for EventSession objects"""

    model = EventSession
    template_name = "event_session_detail.html"
    context_object_name = "session"


class EventSessionUpdateView(
    CampViewMixin,
    ContentTeamPermissionMixin,
    EventSessionFormViewMixin,
    UpdateView,
):
    """This view is used by the Content Team to update EventSession objects"""

    model = EventSession
    fields = ["when", "description", "event_duration_minutes"]
    template_name = "event_session_form.html"

    def form_valid(self, form):
        """Just save, we have a post_save signal which takes care of fixing EventSlots"""
        session = form.save()
        messages.success(self.request, f"{session} has been updated successfully!")
        return redirect(
            reverse(
                "backoffice:event_session_list",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


class EventSessionDeleteView(CampViewMixin, ContentTeamPermissionMixin, DeleteView):
    """This view is used by the Content Team to delete EventSession objects"""

    model = EventSession
    template_name = "event_session_delete.html"
    context_object_name = "session"

    def get(self, *args, **kwargs):
        """Show a warning if we have something scheduled in this EventSession"""
        if self.get_object().event_slots.filter(event__isnull=False).exists():
            messages.warning(
                self.request,
                "NOTE: One or more EventSlots in this EventSession has an Event scheduled. Make sure you are deleting the correct session!",
            )
        return super().get(*args, **kwargs)

    def delete(self, *args, **kwargs):
        session = self.get_object()
        session.event_slots.all().delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            "EventSession and related EventSlots was deleted successfully!",
        )
        return reverse(
            "backoffice:event_session_list",
            kwargs={"camp_slug": self.camp.slug},
        )


################################
# MANAGE EVENTSLOT VIEWS


class EventSlotListView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """This view is used by the Content Team to see EventSlot objects."""

    model = EventSlot
    template_name = "event_slot_list.html"
    context_object_name = "event_slot_list"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.prefetch_related(
            "event__speakers",
            "event_session__event_location",
            "event_session__event_type",
        )
        return qs


class EventSlotDetailView(CampViewMixin, ContentTeamPermissionMixin, DetailView):
    """This view is used by the Content Team to see details for EventSlot objects"""

    model = EventSlot
    template_name = "event_slot_detail.html"
    context_object_name = "event_slot"


class EventSlotUnscheduleView(CampViewMixin, ContentTeamPermissionMixin, UpdateView):
    """This view is used by the Content Team to remove an Event from the schedule/EventSlot"""

    model = EventSlot
    template_name = "event_slot_unschedule.html"
    fields = []
    context_object_name = "event_slot"

    def form_valid(self, form):
        event_slot = self.get_object()
        event = event_slot.event
        event_slot.unschedule()
        messages.success(
            self.request,
            f"The Event '{event.title}' has been removed from the slot {event_slot}",
        )
        return redirect(
            reverse(
                "backoffice:event_detail",
                kwargs={"camp_slug": self.camp.slug, "slug": event.slug},
            ),
        )


################################
# AUTOSCHEDULER VIEWS


class AutoScheduleManageView(CampViewMixin, ContentTeamPermissionMixin, TemplateView):
    """Just an index type view with links to the various actions"""

    template_name = "autoschedule_index.html"


class AutoScheduleCrashCourseView(
    CampViewMixin,
    ContentTeamPermissionMixin,
    TemplateView,
):
    """A short crash course on the autoscheduler"""

    template_name = "autoschedule_crash_course.html"


class AutoScheduleValidateView(CampViewMixin, ContentTeamPermissionMixin, FormView):
    """This view is used to validate schedules. It uses the AutoScheduler and can
    either validate the currently applied schedule or a new similar schedule, or a
    brand new schedule
    """

    template_name = "autoschedule_validate.html"
    form_class = AutoScheduleValidateForm

    def form_valid(self, form):
        kwargs = copy.deepcopy(form.cleaned_data)
        del kwargs["schedule"]

        # initialise AutoScheduler
        scheduler = AutoScheduler(camp=self.camp, **kwargs)
        autoschedule = None

        # get autoschedule
        if form.cleaned_data["schedule"] == "current":
            try:
                autoschedule = scheduler.build_current_autoschedule()
                message = f"The currently scheduled Events form a valid schedule! AutoScheduler has {len(scheduler.autoslots)} Slots based on {scheduler.event_sessions.count()} EventSessions for {scheduler.event_types.count()} EventTypes. {scheduler.events.count()} Events in the schedule."
            except ValueError:
                messages.error(
                    self.request,
                    "Unable to calculate autoschedule, no valid solution found!",
                )
        elif form.cleaned_data["schedule"] == "similar":
            try:
                original_autoschedule = scheduler.build_current_autoschedule()
                autoschedule, diff = scheduler.calculate_similar_autoschedule(
                    original_autoschedule,
                )
                message = f"The new similar schedule is valid! AutoScheduler has {len(scheduler.autoslots)} Slots based on {scheduler.event_sessions.count()} EventSessions for {scheduler.event_types.count()} EventTypes. Differences to the current schedule: {len(diff['event_diffs'])} Event diffs and {len(diff['slot_diffs'])} Slot diffs."
            except ValueError:
                messages.error(
                    self.request,
                    "Unable to calculate autoschedule, no valid solution found!",
                )
        elif form.cleaned_data["schedule"] == "new":
            try:
                autoschedule = scheduler.calculate_autoschedule()
                message = f"The new schedule is valid! AutoScheduler has {len(scheduler.autoslots)} Slots based on {scheduler.event_sessions.count()} EventSessions for {scheduler.event_types.count()} EventTypes. {scheduler.events.count()} Events in the schedule."
            except ValueError:
                messages.error(
                    self.request,
                    "Unable to calculate autoschedule, no valid solution found!",
                )

        if autoschedule:
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
                "backoffice:autoschedule_validate",
                kwargs={"camp_slug": self.camp.slug},
            ),
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
    """This view is used by the Content Team to apply a new schedules by unscheduling
    all autoscheduled Events, and scheduling all Event/Slot combinations in the schedule.

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
            diff = None

        # check validity
        valid, violations = scheduler.is_valid(autoschedule, return_violations=True)
        if valid:
            # schedule is valid, apply it
            deleted, created = scheduler.apply(autoschedule)
            messages.success(
                self.request,
                f"Schedule has been applied! {deleted} Events removed from schedule, {created} new Events scheduled.",
            )
            if diff:
                messages.success(
                    self.request,
                    "Differences to the previous schedule: {len(diff['event_diffs'])} Event diffs and {len(diff['slot_diffs'])} Slot diffs.",
                )
        else:
            messages.error(self.request, "Schedule is NOT valid, cannot apply!")
        return redirect(
            reverse(
                "backoffice:autoschedule_apply",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


class AutoScheduleDebugEventSlotUnavailabilityView(
    CampViewMixin,
    ContentTeamPermissionMixin,
    TemplateView,
):
    template_name = "autoschedule_debug_slots.html"

    def get_context_data(self, **kwargs):
        scheduler = AutoScheduler(camp=self.camp)
        for autoevent, _ in zip(scheduler.autoevents, scheduler.events.all(), strict=False):
            autoevent.possible_slots = 0
            for slot in scheduler.autoslots:
                if slot not in autoevent.unavailability:
                    autoevent.possible_slots += 1
        context = {
            "scheduler": scheduler,
        }
        return context


class AutoScheduleDebugEventConflictsView(
    CampViewMixin,
    ContentTeamPermissionMixin,
    TemplateView,
):
    template_name = "autoschedule_debug_events.html"

    def get_context_data(self, **kwargs):
        scheduler = AutoScheduler(camp=self.camp)
        context = {
            "scheduler": scheduler,
        }
        return context
