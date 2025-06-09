from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

from camps.models import Camp
from program.models import EventInstance
from program.models import EventSession
from program.models import EventSlot
from program.models import SpeakerAvailability

logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    args = "none"
    help = "Migrate eventinstances to eventsessions and eventslots"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "campslug",
            type=str,
            help="The slug of the camp to process",
        )

    def handle(self, *args, **options) -> None:
        camp = Camp.objects.get(slug=options["campslug"])
        for event_type_id in set(
            EventInstance.objects.filter(event__track__camp=camp).values_list(
                "event__event_type",
                flat=True,
            ),
        ):
            if event_type_id == 1:
                # skip facilities
                continue
            logger.info(f"processing event type id {event_type_id} ...")
            for instance in EventInstance.objects.filter(
                event__track__camp=camp,
                event__event_type_id=event_type_id,
            ):
                logger.info(f"processing instance {instance}")

                for speaker in instance.event.speakers.all():
                    # create speaker availability
                    try:
                        sa = SpeakerAvailability.objects.get(
                            speaker=speaker,
                            when__adjacent_to=instance.when,
                            available=True,
                        )
                        if sa.when.lower == instance.when.upper:
                            # this availability begins when the instance ends
                            sa.when = (instance.when.lower, sa.when.upper)
                        else:
                            # this availability ends when the instance begins
                            sa.when = (sa.when.lower, instance.when.upper)
                        sa.save()
                        logger.info(
                            f"extended speakeravailability {sa} for speaker {speaker} to include instance {instance}",
                        )
                    except SpeakerAvailability.DoesNotExist:
                        sa = SpeakerAvailability.objects.create(
                            speaker=speaker,
                            when=instance.when,
                            available=True,
                        )
                        logger.info(
                            f"created speakeravailability {sa} for speaker {speaker} for instance {instance}",
                        )
                    except SpeakerAvailability.MultipleObjectsReturned:
                        # who the hell does three events in a row?!
                        sas = SpeakerAvailability.objects.filter(
                            speaker=speaker,
                            when__adjacent_to=instance.when,
                            available=True,
                        ).order_by("when")
                        sa = SpeakerAvailability(
                            speaker=speaker,
                            when=(sas[0].when.lower, sas[1].when.upper),
                            available=True,
                        )
                        sas.all().delete()
                        sa.save()

                duration = int(
                    (instance.when.upper - instance.when.lower).total_seconds() / 60,
                )
                # do we have a matching slot?
                try:
                    slot = EventSlot.objects.get(
                        when=instance.when,
                        event_session__event_type=instance.event.event_type,
                    )
                except EventSlot.DoesNotExist:
                    slot = None

                if not slot:
                    logger.info(f"no existing slot found for instance {instance}")
                    # do we have a session of the matching type and event duration which is adjacent to this eventinstance?
                    try:
                        session = EventSession.objects.get(
                            when__adjacent_to=instance.when,
                            event_type_id=event_type_id,
                            event_duration_minutes=duration,
                            event_location=instance.location,
                        )
                        logger.info(
                            f"found existing eventsession adjacent to instance {instance}",
                        )
                        if session.when.lower == instance.when.upper:
                            # session starts when this instance ends
                            session.when = (instance.when.lower, session.when.upper)
                        elif session.when.upper == instance.when.lower:
                            # session ends when this instance starts
                            session.when = (session.when.lower, instance.when.upper)
                        logger.info(
                            f"session has been expanded to include instance {instance}",
                        )
                        session.save()
                        # we should now have a matching slot
                        slot = EventSlot.objects.get(
                            when=instance.when,
                            event_session__event_type=instance.event.event_type,
                        )
                    except EventSession.DoesNotExist:
                        session = EventSession.objects.create(
                            camp=camp,
                            event_location=instance.location,
                            event_type=instance.event.event_type,
                            when=instance.when,
                            event_duration_minutes=duration,
                        )
                        logger.info(f"created new eventsession {session}")
                        slot = session.event_slots.get()
                logger.info(f"found slot {slot} matching instance {instance}")
                slot.event = instance.event
                slot.autoscheduled = False
                slot.save()
                logger.info(f"saved slot {slot}")
