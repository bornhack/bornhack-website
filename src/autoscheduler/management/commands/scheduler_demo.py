from datetime import datetime

from conference_scheduler import converter, scheduler
from conference_scheduler.lp_problem import objective_functions
from conference_scheduler.resources import Event, Slot
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = "none"
    help = "conference_autoscheduler demo code"

    def handle(self, *args, **options):
        talk_slots = [
            Slot(
                venue="Big",
                starts_at=datetime(2016, 9, 15, 9, 30),
                duration=30,
                session="A",
                capacity=200,
            ),
            Slot(
                venue="Big",
                starts_at=datetime(2016, 9, 15, 10, 0),
                duration=30,
                session="A",
                capacity=200,
            ),
            Slot(
                venue="Small",
                starts_at=datetime(2016, 9, 15, 9, 30),
                duration=30,
                session="B",
                capacity=50,
            ),
            Slot(
                venue="Small",
                starts_at=datetime(2016, 9, 15, 10, 0),
                duration=30,
                session="B",
                capacity=50,
            ),
            Slot(
                venue="Big",
                starts_at=datetime(2016, 9, 15, 12, 30),
                duration=30,
                session="C",
                capacity=200,
            ),
            Slot(
                venue="Big",
                starts_at=datetime(2016, 9, 15, 13, 0),
                duration=30,
                session="C",
                capacity=200,
            ),
            Slot(
                venue="Small",
                starts_at=datetime(2016, 9, 15, 12, 30),
                duration=30,
                session="D",
                capacity=50,
            ),
            Slot(
                venue="Small",
                starts_at=datetime(2016, 9, 15, 13, 0),
                duration=30,
                session="D",
                capacity=50,
            ),
            Slot(
                venue="Big",
                starts_at=datetime(2016, 9, 16, 9, 30),
                duration=30,
                session="E",
                capacity=50,
            ),
            Slot(
                venue="Big",
                starts_at=datetime(2016, 9, 16, 10, 00),
                duration=30,
                session="E",
                capacity=50,
            ),
            Slot(
                venue="Big",
                starts_at=datetime(2016, 9, 16, 12, 30),
                duration=30,
                session="F",
                capacity=50,
            ),
            Slot(
                venue="Big",
                starts_at=datetime(2016, 9, 16, 13, 0),
                duration=30,
                session="F",
                capacity=50,
            ),
        ]
        workshop_slots = [
            Slot(
                venue="Small",
                starts_at=datetime(2016, 9, 16, 9, 30),
                duration=60,
                session="G",
                capacity=50,
            ),
            Slot(
                venue="Small",
                starts_at=datetime(2016, 9, 16, 13, 0),
                duration=60,
                session="H",
                capacity=50,
            ),
        ]

        outside_slots = [
            Slot(
                venue="Outside",
                starts_at=datetime(2016, 9, 16, 12, 30),
                duration=90,
                session="I",
                capacity=1000,
            ),
            Slot(
                venue="Outside",
                starts_at=datetime(2016, 9, 16, 13, 0),
                duration=90,
                session="J",
                capacity=1000,
            ),
        ]

        slots = talk_slots + workshop_slots + outside_slots

        events = [
            Event(
                name="Talk 1",
                duration=30,
                tags=["beginner"],
                unavailability=outside_slots[:],
                demand=50,
            ),
            Event(
                name="Talk 2",
                duration=30,
                tags=["beginner"],
                unavailability=outside_slots[:],
                demand=130,
            ),
            Event(
                name="Talk 3",
                duration=30,
                tags=["beginner"],
                unavailability=outside_slots[:],
                demand=200,
            ),
            Event(
                name="Talk 4",
                duration=30,
                tags=["beginner"],
                unavailability=outside_slots[:],
                demand=30,
            ),
            Event(
                name="Talk 5",
                duration=30,
                tags=["intermediate"],
                unavailability=outside_slots[:],
                demand=60,
            ),
            Event(
                name="Talk 6",
                duration=30,
                tags=["intermediate"],
                unavailability=outside_slots[:],
                demand=30,
            ),
            Event(
                name="Talk 7",
                duration=30,
                tags=["intermediate", "advanced"],
                unavailability=outside_slots[:],
                demand=60,
            ),
            Event(
                name="Talk 8",
                duration=30,
                tags=["intermediate", "advanced"],
                unavailability=outside_slots[:],
                demand=60,
            ),
            Event(
                name="Talk 9",
                duration=30,
                tags=["advanced"],
                unavailability=outside_slots[:],
                demand=60,
            ),
            Event(
                name="Talk 10",
                duration=30,
                tags=["advanced"],
                unavailability=outside_slots[:],
                demand=30,
            ),
            Event(
                name="Talk 11",
                duration=30,
                tags=["advanced"],
                unavailability=outside_slots[:],
                demand=30,
            ),
            Event(
                name="Talk 12",
                duration=30,
                tags=["advanced"],
                unavailability=outside_slots[:],
                demand=30,
            ),
            Event(
                name="Workshop 1",
                duration=60,
                tags=["testing"],
                unavailability=outside_slots[:],
                demand=40,
            ),
            Event(
                name="Workshop 2",
                duration=60,
                tags=["testing"],
                unavailability=outside_slots[:],
                demand=40,
            ),
            Event(
                name="City tour",
                duration=90,
                tags=[],
                unavailability=talk_slots[:] + workshop_slots[:],
                demand=100,
            ),
            Event(
                name="Boardgames",
                duration=90,
                tags=[],
                unavailability=talk_slots[:] + workshop_slots[:],
                demand=20,
            ),
        ]

        new_events = [
            Event(
                name="Talk 13", duration=30, unavailability=outside_slots[:], demand=30,
            ),
            Event(
                name="Talk 14", duration=30, unavailability=outside_slots[:], demand=30,
            ),
        ]

        new_slots = [
            Slot(
                venue="Big",
                starts_at=datetime(2016, 9, 15, 13, 30),
                duration=30,
                session="C",
                capacity=200,
            ),
            Slot(
                venue="Big",
                starts_at=datetime(2016, 9, 15, 14, 0),
                duration=30,
                session="C",
                capacity=200,
            ),
        ]

        schedule = scheduler.schedule(events, slots)
        schedule.sort(key=lambda item: item.slot.starts_at)
        print("---- first schedule ---")
        for item in schedule:
            print(f"{item.event.name} at {item.slot.starts_at} in {item.slot.venue}")

        # we need the original schedule unaltered for the diff,
        # but for the new calculation we need it with the removed events and slots removed
        orig_schedule = schedule.copy()

        # first get the schedule as a <class 'numpy.ndarray'>
        array = converter.schedule_to_array(
            schedule=schedule, events=events, slots=slots,
        )
        # convert it to a list of lists of booleans
        matrix = [list(x) for x in array]

        # make a slot unavailable
        print(f"deleting slot: {slots[10]}")
        del slots[10]
        # also remove the deleted slots column from all rows of the old schedule
        for row in matrix:
            del [row[10]]

        # add some new unavailability to an event
        events[10].add_unavailability(*slots[9:])

        # lets cancel an event as well
        print(f"deleting event: {events[8]}")
        del events[6]
        # also remove the events row from the original schedule
        del matrix[6]

        # add 2 new events and 2 slots
        events += new_events
        slots += new_slots

        # build the "new" original schedule object with the new list of events and slots
        schedule = converter.array_to_schedule(
            array=matrix, events=events, slots=slots,
        )

        similar_schedule = scheduler.schedule(
            events,
            slots,
            objective_function=objective_functions.number_of_changes,
            original_schedule=schedule,
        )
        similar_schedule.sort(key=lambda item: item.slot.starts_at)
        print("---- second schedule ---")
        for item in similar_schedule:
            print(f"{item.event.name} at {item.slot.starts_at} in {item.slot.venue}")

        print("---- slot diff ---")
        slot_diff = scheduler.slot_schedule_difference(orig_schedule, similar_schedule)
        for item in slot_diff:
            if item.new_event and item.old_event:
                print(
                    f"{item.slot.venue} at {item.slot.starts_at} will now host {item.new_event.name} rather than {item.old_event.name}"
                )
            elif item.new_event and not item.old_event:
                print(
                    f"{item.slot.venue} at {item.slot.starts_at} will now host {item.new_event.name} instead of hosting nothing"
                )
            elif not item.new_event and item.old_event:
                print(
                    f"{item.slot.venue} at {item.slot.starts_at} will now host nothing instead of hosting {item.old_event.name}"
                )

        print("---- event diff ---")
        event_diff = scheduler.event_schedule_difference(
            orig_schedule, similar_schedule
        )
        for item in event_diff:
            if item.old_slot and item.new_slot:
                print(
                    f"{item.event.name} has moved from {item.old_slot.venue} at {item.old_slot.starts_at} to {item.new_slot.venue} at {item.new_slot.starts_at}"
                )
            elif item.old_slot and not item.new_slot:
                print(
                    f"{item.event.name} has moved from {item.old_slot.venue} at {item.old_slot.starts_at} to not being scheduled anymore"
                )
            elif not item.old_slot and item.new_slot:
                print(
                    f"{item.event.name} was not scheduled before but is now scheduled in {item.new_slot.venue} at {item.new_slot.starts_at}"
                )
            else:
                print("what is happening")
