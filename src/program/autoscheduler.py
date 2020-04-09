import logging
from datetime import timedelta

from conference_scheduler import resources, scheduler
from conference_scheduler.lp_problem import objective_functions
from conference_scheduler.validator import is_valid_schedule, schedule_violations
from psycopg2.extras import DateTimeTZRange

from .models import EventType

logger = logging.getLogger("bornhack.%s" % __name__)


class AutoScheduler:
    """
    The BornHack AutoScheduler. Made with love by Tykling.

    Built around https://github.com/PyconUK/ConferenceScheduler which works with lists
    of conference_scheduler.resources.Slot and conference_scheduler.resources.Event objects.

    Most of the code in this class deals with massaging our data into a list of Slot and
    Event objects defining the data and constraints for the scheduler.

    Initialising this class takes a while because all the objects have to be created.
    """

    def __init__(self, camp):
        """ Get EventTypes, EventSessions and Events, build autoslot and autoevent objects """
        self.camp = camp

        # Get all EventTypes which support autoscheduling
        self.event_types = self.get_event_types()

        # Get all EventSessions for the current event_types
        self.event_sessions = self.get_event_sessions(self.event_types)

        # Build a lookup dict of lists of EventSession IDs per EventType (for easy lookups later)
        self.eventtype_sessions = {}
        for session in self.event_sessions:
            if session.event_type not in self.eventtype_sessions:
                self.eventtype_sessions[session.event_type] = []
            self.eventtype_sessions[session.event_type].append(session.id)

        # Get all Events for the current event_types
        self.events = self.get_events(self.event_types)

        # Get autoslots
        self.autoslots = self.get_autoslots(self.event_sessions)

        # Build a lookup dict of autoslots per EventType
        self.eventtype_slots = {}
        for autoslot in self.autoslots:
            # loop over eventtype_sessions dict and find our
            for et, sessions in self.eventtype_sessions.items():
                if autoslot.session in sessions:
                    if et not in self.eventtype_slots:
                        self.eventtype_slots[et] = []
                    self.eventtype_slots[et].append(autoslot)
                    break

        # get autoevents and a lookup dict which maps Event id to autoevent index
        self.autoevents, self.autoeventindex = self.get_autoevents(self.events)

    def get_event_types(self):
        """ Return all EventTypes which support autoscheduling """
        return EventType.objects.filter(support_autoscheduling=True)

    def get_event_sessions(self, event_types):
        """ Return all EventSessions for these EventTypes """
        return self.camp.eventsessions.filter(
            event_type__in=event_types,
        ).prefetch_related("event_type", "event_location")

    def get_events(self, event_types):
        """ Return all Events for the event_types, exclude any manually scheduled Events """
        return self.camp.events.filter(event_type__in=event_types).exclude(
            # but exclude Events that already have one or more EventInstances...
            instances__isnull=False,
            # ...unless those eventinstances are autoscheduled
            instances__autoscheduled=False,
        )

    def get_autoslots(self, event_sessions):
        """ Return a list of autoslots for all slots in all EventSessions """
        autoslots = []
        # loop over the sessions
        for session in event_sessions:
            # loop over slots in this session
            for slot in session.get_available_slots(count_autoscheduled_as_free=True):
                autoslots.append(
                    resources.Slot(
                        venue=session.event_location.id,
                        starts_at=slot.lower,
                        duration=int((slot.upper - slot.lower).total_seconds() / 60),
                        session=session.id,
                        capacity=session.event_location.capacity,
                    )
                )
        return autoslots

    def get_autoevents(self, events):
        """ Return a list of resources.Event objects, one for each Event """
        autoevents = []
        autoeventindex = {}
        for event in events:
            autoevents.append(
                resources.Event(
                    name=event.id,
                    duration=event.get_duration(),
                    tags=[],
                    demand=event.demand,
                )
            )
            # create a dict of events with the autoevent index as key and the Event as value
            autoeventindex[autoevents.index(autoevents[-1])] = event

        # loop over all autoevents to add unavailability...
        # (we have to do this in a seperate loop because we need all the autoevents to exist)
        for autoevent in autoevents:
            # get the Event
            event = autoeventindex[autoevents.index(autoevent)]
            # loop over all other eventtypes...
            for et in self.event_types.all().exclude(pk=event.event_type.pk):
                if et in self.eventtype_slots:
                    # and add all slots for this EventType as unavailable for this event,
                    # this means we don't schedule a talk in a workshop slot and vice versa.
                    autoevent.add_unavailability(*self.eventtype_slots[et])

            # loop over all speakers for this event and add event conflicts
            for speaker in event.speakers.all():
                # loop over other events featuring this speaker, register each conflict
                conflict_ids = speaker.events.exclude(id=event.id).values_list(
                    "id", flat=True
                )
                for conflictevent in autoevents:
                    # only the event with the lowest index gets the unavailability
                    if conflictevent.name in conflict_ids:
                        if autoevents.index(conflictevent) > autoevents.index(
                            autoevent
                        ):
                            autoevent.add_unavailability(conflictevent)

                # Register all slots where we have no positive availability
                # for this speaker as unavailable
                available = []
                for availability in speaker.availabilities.filter(
                    available=True
                ).values_list("when", flat=True):
                    availability = DateTimeTZRange(
                        availability.lower, availability.upper, "()"
                    )
                    for slot in self.autoslots:
                        slotrange = DateTimeTZRange(
                            slot.starts_at,
                            slot.starts_at + timedelta(minutes=slot.duration),
                            "()",
                        )
                        if slotrange in availability:
                            # the speaker is available for this slot
                            available.append(self.autoslots.index(slot))
                autoevent.add_unavailability(
                    *[
                        s
                        for s in self.autoslots
                        if not self.autoslots.index(s) in available
                    ]
                )

        return autoevents, autoeventindex

    def build_current_autoschedule(self):
        """ Build an autoschedule object based on existing EventInstances.
        Returns an autoschedule, which is a list of conference_scheduler.resources.ScheduledItem
        objects, one for each EventInstance. This function is useful for creating an "original
        schedule" to base a new similar schedule off of. """

        # loop over eventsinstances and create a ScheduledItem object for each
        autoschedule = []
        for instance in self.camp.event_instances.filter(event__in=self.events):
            for autoevent in self.autoevents:
                if autoevent.name == instance.event.id:
                    # we need the index number of the event
                    eventindex = self.autoevents.index(autoevent)
                    break
            # loop over the autoslots to find the one this event is scheduled in
            scheduled = False
            for autoslot in self.autoslots:
                if (
                    autoslot.venue == instance.location.id
                    and autoslot.starts_at == instance.when.lower
                    and autoslot.session
                    in self.eventtype_sessions[instance.event.event_type]
                ):
                    # This slot starts at the same time as the EventInstance, and at the same
                    # location. It also has the session ID of a session with the right EventType.
                    autoschedule.append(
                        resources.ScheduledItem(
                            event=self.autoevents[eventindex],
                            slot=self.autoslots[self.autoslots.index(autoslot)],
                        )
                    )
                    scheduled = True
                    break

            # did we find a slot matching this EventInstance?
            if not scheduled:
                print(f"Could not find a slot for EventInstance {instance} - skipping")

        # The returned schedule might not be valid! For example if a speaker is no
        # longer available when their talk is scheduled. This is fine though, an invalid
        # schedule can still be used as a basis for creating a new similar schedule.
        return autoschedule

    def calculate_autoschedule(self, original_schedule=None):
        """ Calculate autoschedule based on self.autoevents and self.autoslots,
            optionally using original_schedule to minimise changes """
        kwargs = {}
        kwargs["events"] = self.autoevents
        kwargs["slots"] = self.autoslots

        # include another schedule in the calculation?
        if original_schedule:
            kwargs["original_schedule"] = original_schedule
            kwargs["objective_function"] = objective_functions.number_of_changes
        else:
            # otherwise use the capacity demand difference thing
            kwargs[
                "objective_function"
            ] = objective_functions.efficiency_capacity_demand_difference
        # calculate the new schedule
        autoschedule = scheduler.schedule(**kwargs)
        return autoschedule

    def calculate_similar_autoschedule(self, original_schedule=None):
        """ Convenience method for creating similar schedules. If original_schedule
        is omitted the new schedule is based on the current schedule instead """

        if not original_schedule:
            # we do not have an original_schedule, use current EventInstances
            original_schedule = self.build_current_autoschedule()

        # calculate and return
        autoschedule = self.calculate_autoschedule(original_schedule=original_schedule)
        diff = self.diff(original_schedule, autoschedule)
        return autoschedule, diff

    def apply(self, autoschedule):
        """ Apply an autoschedule by creating EventInstance objects to match it """

        # "The Clean Slate protocol sir?" - delete any existing autoscheduled EventInstances
        # TODO: investigate how this affects the FRAB XML export (for which we added a UUID on
        # EventInstance objects). Make sure "favourite" functionality or bookmarks or w/e in
        # FRAB clients still work after a schedule "re"apply. We might need a smaller hammer here.
        deleted, details = self.camp.event_instances.filter(autoscheduled=True).delete()

        # loop and create eventinstances
        created = 0
        for item in autoschedule:
            # item is an instance of conference_scheduler.resources.ScheduledItem
            event = self.camp.events.get(id=item.event.name)
            location = self.camp.event_locations.get(id=int(item.slot.venue))
            self.camp.event_instances.create(
                event=event,
                when=DateTimeTZRange(
                    item.slot.starts_at,
                    item.slot.starts_at + timedelta(minutes=item.slot.duration),
                ),
                location=location,
                autoscheduled=True,
            )
            created += 1

        # return the numbers
        return deleted, created

    def diff(self, original_schedule, new_schedule):
        """
        This method returns a dict of Event differences and Slot differences between
        the two schedules.
        """
        slot_diff = scheduler.slot_schedule_difference(original_schedule, new_schedule,)

        slot_output = []
        for item in slot_diff:
            slot_output.append(
                {
                    "eventlocation": self.camp.eventlocations.get(pk=item.slot.venue),
                    "starttime": item.slot.starts_at,
                    "old": {},
                    "new": {},
                }
            )
            if item.old_event:
                try:
                    old_event = self.camp.events.get(pk=item.old_event.name)
                except self.camp.events.DoesNotExist:
                    old_event = item.old_event.name
                slot_output[-1]["old"]["event"] = old_event
            if item.new_event:
                try:
                    new_event = self.camp.events.get(pk=item.new_event.name)
                except self.camp.events.DoesNotExist:
                    new_event = item.old_event.name
                slot_output[-1]["new"]["event"] = new_event

        # then get a list of differences per event
        event_diff = scheduler.event_schedule_difference(
            original_schedule, new_schedule,
        )
        event_output = []
        # loop over the differences and build the dict
        for item in event_diff:
            try:
                event = self.camp.events.get(pk=item.event.name)
            except self.camp.events.DoesNotExist:
                event = item.event.name
            event_output.append(
                {"event": event, "old": {}, "new": {},}
            )
            # do we have an old slot for this event?
            if item.old_slot:
                event_output[-1]["old"]["eventlocation"] = self.camp.eventlocations.get(
                    id=item.old_slot.venue
                )
                event_output[-1]["old"]["starttime"] = item.old_slot.starts_at
            # do we have a new slot for this event?
            if item.new_slot:
                event_output[-1]["new"]["eventlocation"] = self.camp.eventlocations.get(
                    id=item.new_slot.venue
                )
                event_output[-1]["new"]["starttime"] = item.new_slot.starts_at

        # all good
        return {"event_diffs": event_output, "slot_diffs": slot_output}

    def is_valid(self, autoschedule, return_violations=False):
        """ Check if a schedule is valid, optionally returning a list of violations if invalid """
        valid = is_valid_schedule(
            autoschedule, slots=self.autoslots, events=self.autoevents
        )
        if not return_violations:
            return valid
        return (
            valid,
            schedule_violations(
                autoschedule, slots=self.autoslots, events=self.autoevents
            ),
        )
