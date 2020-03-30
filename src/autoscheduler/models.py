from datetime import timedelta

import program.models
from conference_scheduler import converter, resources, scheduler
from conference_scheduler.lp_problem import objective_functions
from django.contrib import messages
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from program.utils import get_slots
from psycopg2._range import DateTimeTZRange
from utils.models import CampRelatedModel


class AutoSchedule(CampRelatedModel):
    """
    Eventually contains the result of an autoscheduler calculation,
    in matrix form.
    """

    class Meta:
        ordering = ["created"]

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="The user who created this Schedule",
    )

    camp = models.ForeignKey(
        "camps.Camp",
        related_name="autoschedules",
        on_delete=models.PROTECT,
        help_text="The Camp this schedule belongs to",
    )

    event_type = models.ForeignKey(
        "program.EventType",
        related_name="autoschedules",
        on_delete=models.PROTECT,
        help_text="The EventType this schedule is for",
    )

    matrix = ArrayField(
        ArrayField(models.BooleanField()),
        blank=True,
        null=True,
        help_text="The matrix representing the calculated schedule. An array of arrays of booleans.",
    )

    applied = models.DateTimeField(
        default=None,
        null=True,
        blank=True,
        help_text="When this schedule was last applied",
    )

    readonly = models.BooleanField(
        default=False,
        blank=True,
        help_text="Is this AutoSchedule readonly? This is set when the schedule is applied.",
    )

    def __str__(self):
        return f"AutoSchedule {self.id} created by {self.user} at {self.created} and last applied {self.applied}"

    def create_autoscheduler_objects(self):
        """ This method loops over events of the given type and creates the related objects
            needed by the autoscheduler.
        """
        # clean slate
        slotsdeleted, slotdetails = self.slots.all().delete()
        eventsdeleted, eventdetails = self.events.all().delete()

        # loop over camp sessions, creatint Slots in the database as we go
        unavailable_slots = set()
        for session in self.camp.eventsessions.filter(event_type=self.event_type):
            for slot in get_slots(session.when, self.event_type.event_duration_minutes):
                # create slot in database
                dbslot = AutoSlot.objects.create(
                    schedule=self,
                    venue=session.event_location.id,
                    starts_at=slot.lower,
                    duration=int((slot.upper - slot.lower).total_seconds() / 60),
                    session=session.id,
                    capacity=session.event_location.capacity,
                )

                # check if this slot at this location is taken by something else
                # (something could be manually scheduled)
                if program.models.EventInstance.objects.filter(
                    location=session.event_location,
                    when__overlap=slot,
                    autoscheduled=False,
                ).exists():
                    # something has been manually scheduled on this location in this slot
                    unavailable_slots.add(dbslot)

        # loop over all Events of the current eventtype and create an AutoEvent object for each
        for event in self.camp.events.filter(event_type=self.event_type).order_by(
            "created"
        ):
            autoevent = AutoEvent.objects.create(
                schedule=self,
                name=event.id,
                event=event,
                duration=event.get_duration(),
                tags=[],
                demand=event.demand,
            )
            for slot in unavailable_slots:
                autoevent.unavailability_slots.add(slot)

        # loop over events again, this time to look for speaker conflicts and unavailability
        # (we have to do this in a seperate loop because we need all the events to exist in db)
        for event in self.camp.events.filter(event_type=self.event_type):
            autoevent = AutoEvent.objects.get(schedule=self, name=event.id)
            # loop over speakers for this event and add unavailability
            for speaker in event.speakers.all():
                # loop over other events featuring this speaker, register each conflict
                for conflict in self.camp.events.filter(speakers=speaker).exclude(
                    id=event.id
                ):
                    # conflict has the same speaker as the current event, register unavailability
                    autoevent.unavailability_events.add(
                        self.events.get(name=conflict.id)
                    )
                # loop over SpeakerAvailability for this speaker (unavailability really)
                for session in self.camp.eventsessions.filter(
                    event_type=self.event_type
                ):
                    # loop over all slots in this session, add unavailability as we go
                    for slot in session.slots:
                        if not speaker.availabilities.filter(
                            # we want to add unavailability unless we have a SpeakerAvailability object which contains all of this slot
                            available=True,
                            when__contains=slot,
                        ).exists():
                            # either we have no SpeakerAvailability for this slot, or the speaker is unavailable
                            autoevent.unavailability_slots.add(
                                self.slots.get(starts_at=slot.lower)
                            )
        # done - return some stats
        if "autoscheduler.AutoSlot" in slotdetails:
            slotsdeleted = slotdetails["autoscheduler.AutoSlot"]
        else:
            slotsdeleted = 0

        if "autoscheduler.AutoEvent" in eventdetails:
            eventsdeleted = eventdetails["autoscheduler.AutoEvent"]
        else:
            eventsdeleted = 0
        return slotsdeleted, eventsdeleted, self.slots.count(), self.events.count()

    def get_autoscheduler_events(self):
        """ Return a list of conference_autoscheduler.resources.Event objects """
        return [event.get_autoscheduler_object() for event in self.events.all()]

    def get_autoscheduler_slots(self):
        """ Return a list of conference_autoscheduler.resources.Slot objects """
        return [slot.get_autoscheduler_object() for slot in self.slots.all()]

    def calculate_autoschedule(self, original_schedule=None):
        """ Calculate, save and return the schedule """
        # start putting kwargs together
        kwargs = {
            "events": self.get_autoscheduler_events(),
            "slots": self.get_autoscheduler_slots(),
        }

        # include another schedule in the calculation?
        if original_schedule:
            # To create a derived schedule based on original_schedule we need
            # to jump through a few hoops to make the scheduler happy.
            # We need to loop over old slots and events to see if any disappeared.
            # - If an event disappeared we remove the corresponding row from the old schedule matrix
            # - If a slot disappeared we remove the coresponding column from all rows in the old schedule matrix

            # first get the original schedule as a <class 'numpy.ndarray'>
            array = converter.schedule_to_array(
                schedule=original_schedule.get_autoschedule(),
                events=original_schedule.get_autoscheduler_events(),
                slots=original_schedule.get_autoscheduler_slots(),
            )
            # and convert that ndarray to a list of lists of booleans
            matrix = [list(x) for x in array]

            # we use program.Event.id as Event name for the autoscheduler objects,
            # we build a list of them all for easy lookups in the loop
            event_list = self.events.all().values_list("name", flat=True)

            # loop over events in the original schedule and see if any were removed
            eventindex = 0
            for event in original_schedule.events.all():
                if event.name not in event_list:
                    # this event was in the old schedule but is not in the new,
                    # we have to delete the corresponding row from the matrix
                    del matrix[eventindex]
                eventindex += 1

            # we use the starttime as lookup key here, so build a list of all the
            # starttimes for easy lookups in the loop
            starttime_list = self.slots.all().values_list("starts_at", flat=True)

            # loop over slots in the original schedule and see if any were removed
            slotindex = 0
            for slot in original_schedule.slots.all():
                if slot.starts_at not in starttime_list:
                    # this slot was in the old schedule but is not in the new,
                    # we have to delete the corresponding column from each row
                    for row in matrix:
                        # delete the column from each row
                        del row[slotindex]
                slotindex += 1

            # build the autoschedule object from the updated matrix and the new
            # list of events and slots
            kwargs["original_schedule"] = converter.array_to_schedule(
                array=matrix,
                events=self.get_autoscheduler_events(),
                slots=self.get_autoscheduler_slots(),
            )

            # include the objective_function for derived schedules
            # (schedules based on a previous schedule)
            kwargs["objective_function"] = objective_functions.number_of_changes
            # from autoscheduler.scheduler import number_of_changes
            # kwargs["objective_function"] = number_of_changes

        # calculate the new schedule
        autoschedule = scheduler.schedule(**kwargs)

        # first get the schedule as a <class 'numpy.ndarray'>
        array = converter.schedule_to_array(
            schedule=autoschedule,
            events=self.get_autoscheduler_events(),
            slots=self.get_autoscheduler_slots(),
        )

        # convert the new schedule to a list of lists of booleans suitable for saving in the DB
        self.matrix = [list(x) for x in array]

        # and save the calculated schedule in DB in ArrayField
        self.save()
        return autoschedule

    def get_autoschedule(self, original_schedule=None):
        """ Returns a conference_autoscheduler.resources.Schedule object """
        if not self.matrix:
            # this schedule has not yet been calculated, lets do that now,
            # which also saves the calculated matrix in self.matrix for next time
            autoschedule = self.calculate_autoschedule(original_schedule)
        else:
            # this schedule has already been calculated, the result is in self.matrix
            autoschedule = converter.array_to_schedule(
                array=self.matrix,
                events=self.get_autoscheduler_events(),
                slots=self.get_autoscheduler_slots(),
            )
        return autoschedule

    def apply(self, original_schedule=None):
        """ Apply this schedule to our program by creating EventInstance objects to match it """
        # get autoschedule
        autoschedule = self.get_autoschedule(original_schedule)

        # "The Clean Slate protocol sir?" - delete any existing autoscheduled EventInstance
        # objects, but only the ones for the current EventType.
        # TODO: investigate how this affects the FRAB XML export (for which we added a UUID on
        # EventInstance objects). Make sure "favourite" functionality or bookmarks or w/e in
        # FRAB clients still work after a schedule "re"apply. We might need a smaller hammer here.
        deleted, details = program.models.EventInstance.objects.filter(
            event__track__camp=self.camp,
            event__event_type=self.event_type,
            autoscheduled=True,
        ).delete()

        # loop and create eventinstances
        created = 0
        for item in autoschedule:
            # item is an instance of conference_scheduler.resources.SheduledItem
            event = program.models.Event.objects.get(id=item.event.name)
            program.models.EventInstance.objects.create(
                event=event,
                when=DateTimeTZRange(
                    item.slot.starts_at,
                    item.slot.starts_at + timedelta(minutes=item.slot.duration),
                ),
                location=program.models.EventLocation.objects.get(id=item.slot.venue),
                autoscheduled=True,
            )
            created += 1
        # mark as applied, which also makes it readonly
        self.applied = timezone.now()
        self.save()

        # return the numbers
        return deleted, created

    def diff(self, previous_schedule):
        """ Output the difference between this schedule and the previous """
        # the conference_autoscheduler supports showing the schedule differences
        # in two ways, first get a list of differences per slot
        slot_diff = scheduler.slot_schedule_difference(
            previous_schedule.get_autoschedule(), self.get_autoschedule(),
        )
        slot_output = []
        for item in slot_diff:
            slot_output.append(
                {
                    "eventlocation": program.models.EventLocation.objects.get(
                        id=item.slot.venue
                    ),
                    "starttime": item.slot.starts_at,
                    "old": {},
                    "new": {},
                }
            )
            if item.old_event:
                slot_output[-1]["old"]["event"] = program.models.Event.objects.get(
                    id=item.old_event.name
                )
            if item.new_event:
                slot_output[-1]["new"]["event"] = program.models.Event.objects.get(
                    id=item.new_event.name
                )

        # then get a list of differences per event
        event_diff = scheduler.event_schedule_difference(
            previous_schedule.get_autoschedule(), self.get_autoschedule(),
        )
        event_output = []
        # loop over the differences and build the dict
        for item in event_diff:
            event_output.append(
                {
                    "event": program.models.Event.objects.get(id=item.event.name),
                    "old": {},
                    "new": {},
                }
            )
            # do we have an old slot for this event?
            if item.old_slot:
                event_output[-1]["old"][
                    "eventlocation"
                ] = program.models.EventLocation.objects.get(id=item.old_slot.venue)
                event_output[-1]["old"]["starttime"] = item.old_slot.starts_at
            # do we have a new slot for this event?
            if item.new_slot:
                event_output[-1]["new"][
                    "eventlocation"
                ] = program.models.EventLocation.objects.get(id=item.new_slot.venue)
                event_output[-1]["new"]["starttime"] = item.new_slot.starts_at

        # all good
        return {"event_diffs": event_output, "slot_diffs": slot_output}

    def print(self):
        """ Used for showing a schedule as plain text when debugging on the console """
        schedule = self.get_autoschedule()
        schedule.sort(key=lambda item: item.slot.starts_at)
        for item in schedule:
            print(
                f"Event {item.event.name} begins at {item.slot.starts_at} in EventLocation {item.slot.venue}"
            )

    def save(self, **kwargs):
        """
        If this object already exists in the database and "applied" is not null,
        then we refuse to save, because we do not permit changes to an applied schedule.
        """
        if self.readonly:
            # this schedule is readonly, no changes allowed
            message = "This schedule is readonly, it can no longer be modified"
            if hasattr(self, "request"):
                messages.error(self.request, message)
            raise ValidationError(message)

        if self.applied and not self.readonly:
            # autoschedule has been applied, mark as readonly
            self.readonly = True

        # go ahead with the save
        super().save(**kwargs)


class AutoEvent(CampRelatedModel):
    """
    This model holds the data we need to reconstruct
    conference_scheduler.resources.Event objects.
    We order by created datetime field to ensure consitent
    ordering (important for the autoscheduler).
    """

    class Meta:
        ordering = ["created"]

    schedule = models.ForeignKey(
        "autoscheduler.AutoSchedule",
        related_name="events",
        help_text="The schedule to which this event belongs",
        on_delete=models.CASCADE,
    )

    name = models.PositiveIntegerField(help_text="The ID of the program.Event object",)

    event = models.ForeignKey(
        "program.Event",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The program.Event object this AutoEvent belongs to. This field is set to None if the related Event is deleted.",
    )

    duration = models.PositiveIntegerField(
        help_text="The duration of this Event (in minutes)",
    )

    tags = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        help_text="List of tags for this Event",
    )

    demand = models.PositiveIntegerField(
        help_text="The number of people going to this event",
    )

    unavailability_events = models.ManyToManyField(
        "self",
        symmetrical=False,
        help_text="Select the events which this event conflicts with",
    )

    unavailability_slots = models.ManyToManyField(
        "autoscheduler.AutoSlot",
        symmetrical=False,
        help_text="Select the slots which are unavailable for this event",
    )

    def __str__(self):
        return f"event {self.name}"

    @property
    def camp(self):
        return self.schedule.camp

    camp_filter = "schedule__camp"

    def get_autoscheduler_object(self, include_unavailability=True):
        event = resources.Event(
            name=self.name,
            duration=self.duration,
            tags=list(self.tags),
            demand=self.demand,
        )
        if include_unavailability:
            for conflict in self.unavailability_events.all():
                event.add_unavailability(
                    conflict.get_autoscheduler_object(include_unavailability=False)
                )
            for slot in self.unavailability_slots.all():
                event.add_unavailability(slot.get_autoscheduler_object())
        return event

    def save(self, **kwargs):
        if self.schedule.applied:
            # this schedule has already been applied, no changes allowed
            message = "This schedule to which this Slot belongs has been applied and can no longer be modified (including related Slots)"
            if hasattr(self, "request"):
                messages.error(self.request, message)
            raise ValidationError(message)
        super().save(**kwargs)


class AutoSlot(CampRelatedModel):
    """
    This model holds the data we need to reconstruct
    conference_scheduler.resources.Slot objects.
    We order by created datetime field to ensure consitent
    ordering (important for the autoscheduler).
    """

    class Meta:
        ordering = ["created"]

    schedule = models.ForeignKey(
        "autoscheduler.AutoSchedule",
        related_name="slots",
        help_text="The schedule to which this slot belongs",
        on_delete=models.CASCADE,
    )

    venue = models.PositiveIntegerField(
        help_text="The ID of the EventLocation this Slot is for"
    )

    starts_at = models.DateTimeField(help_text="The start time of this Slot")

    duration = models.PositiveIntegerField(
        help_text="The duration of this Slot (in minutes)",
    )

    session = models.PositiveIntegerField(
        help_text="The ID of the EventSession object this Slot is part of"
    )

    capacity = models.PositiveIntegerField(
        help_text="The capacity of the EventLocation this Slot is for"
    )

    @property
    def camp(self):
        return self.schedule.camp

    camp_filter = "schedule__camp"

    def __str__(self):
        return f"AutoSlot {self.id} for EventLocation {self.venue} starting at {self.starts_at}"

    def get_autoscheduler_object(self):
        return resources.Slot(
            venue=self.venue,
            starts_at=self.starts_at,
            duration=self.duration,
            session=self.session,
            capacity=self.capacity,
        )

    def save(self, **kwargs):
        if self.schedule.applied:
            # this schedule has already been applied, no changes allowed
            message = "This schedule to which this Event belongs has been applied and can no longer be modified (including related Events)"
            if hasattr(self, "request"):
                messages.error(self.request, message)
            raise ValidationError(message)
        super().save(**kwargs)
