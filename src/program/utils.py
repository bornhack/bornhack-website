from __future__ import annotations

import datetime
import logging
from collections import OrderedDict
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from zoneinfo import ZoneInfo
from psycopg2.extras import DateTimeTZRange

logger = logging.getLogger(f"bornhack.{__name__}")


def get_daychunks(day):
    """Given a DateTimeTZRange day returns a list of "daychunks" which are
    DateTimeTZRanges of length settings.SPEAKER_AVAILABILITY_DAYCHUNK_HOURS
    starting from day.lower. If day.lower is midnight and day.upper is 10 AM and
    settings.SPEAKER_AVAILABILITY_DAYCHUNK_HOURS=2 then a list of 5 daychunks
    would be returned.
    """
    chunks = []
    daychunk = DateTimeTZRange(
        day.lower,
        day.lower + timedelta(hours=settings.SPEAKER_AVAILABILITY_DAYCHUNK_HOURS),
    )
    i = 0
    while daychunk.upper < day.upper:
        # append this chunk
        chunks.append(daychunk)
        # increase our counter
        i += 1
        daychunk = DateTimeTZRange(
            day.lower + timedelta(hours=settings.SPEAKER_AVAILABILITY_DAYCHUNK_HOURS * i),
            day.lower + timedelta(hours=settings.SPEAKER_AVAILABILITY_DAYCHUNK_HOURS * (i + 1)),
        )

    # cap the final chunk to be equal to the end of the day
    daychunk = DateTimeTZRange(
        day.lower + timedelta(hours=settings.SPEAKER_AVAILABILITY_DAYCHUNK_HOURS * i),
        min(
            day.lower + timedelta(hours=settings.SPEAKER_AVAILABILITY_DAYCHUNK_HOURS * (i + 1)),
            day.upper,
        ),
    )

    # append the final chunk and return
    chunks.append(daychunk)
    return chunks


def get_speaker_availability_form_matrix(sessions):
    """Create a speaker availability matrix of columns, rows and checkboxes for the HTML form.

    Returns a "matrix" - a dict of dicts, where the outer dict keys are DateTimeTZRanges
    representing a full camp "day" (as returned by camp.get_days("camp")), and the
    value is an OrderedDict of chunks based on settings.SPEAKER_AVAILABILITY_DAYCHUNK_HOURS
    with the daychunk DateTimeTZRange as key and a value which is None if we don't want a checkbox,
    or a dict with "fieldname" (string) and "event_types" (list) and "available" (bool) if we do.

    For example, with a 2 day camp and settings.SPEAKER_AVAILABILITY_DAYCHUNK_HOURS=12
    and 24h EventSessions for both days he matrix dict would have 2 members (one per day),
    and each would be an OrderedDict with 2 members (one per 12 hour daychunk).
    """
    # start with an empty dict
    matrix = OrderedDict()

    if not sessions:
        return matrix

    # loop over days in the camp
    for day in get_tzrange_days(tzranges=[s.when for s in sessions]):
        # loop over the daychunks in this day
        for daychunk in get_daychunks(day):
            event_types = set()
            for session in sessions:
                # add the event_type if this session overlaps with daychunk
                if daychunk & session.when:
                    event_types.add(session.event_type)

            # make sure we already have an OrderedDict for this day in the matrix
            if day not in matrix:
                matrix[day] = OrderedDict()

            # skip this chunk if we found no sessions
            if event_types:
                # build the dict for this daychunk
                matrix[day][daychunk] = {}
                matrix[day][daychunk]["fieldname"] = (
                    f"availability_{daychunk.lower.strftime('%Y_%m_%d_%H_%M')}_to_{daychunk.upper.strftime('%Y_%m_%d_%H_%M')}"
                )
                matrix[day][daychunk]["event_types"] = []
                # pass a list of dicts instead of the queryset to avoid one million lookups
                for et in event_types:
                    matrix[day][daychunk]["event_types"].append(
                        {
                            "name": et.name,
                            "icon": et.icon,
                            "color": et.color,
                        },
                    )
                matrix[day][daychunk]["initial"] = None
            else:
                # no sessions for this chunk, no checkbox needed
                matrix[day][daychunk] = None

    # Due to the way we build the matrix it is not trivial to avoid adding days
    # where none of the chunks need a checkbox. Loop over and remove any days with
    # 0 checkboxes before returning
    new_matrix = matrix.copy()
    for date in matrix:
        for chunk in matrix[date]:
            if matrix[date][chunk]:
                # we have at least one checkbox on this date, keep it
                break
        else:
            # we looped over all chunks on this day and we need 0 checkboxes
            del new_matrix[date]

    return new_matrix


def save_speaker_availability(form, obj) -> None:
    """Called from SpeakerProposalCreateView, SpeakerProposalUpdateView,
    and CombinedProposalSubmitView to create SpeakerProposalAvailability
    objects based on the submitted form.
    Also called from SpeakerUpdateView in backoffice to update
    SpeakerAvailability.
    Starts out by deleting all existing availability before saving form.
    """
    if hasattr(obj, "proposal"):
        # obj is a Speaker
        AvailabilityModel = apps.get_model("program", "SpeakerAvailability")
        kwargs = {"speaker": obj}
    else:
        # obj is a SpeakerProposal
        AvailabilityModel = apps.get_model("program", "SpeakerProposalAvailability")
        kwargs = {"speaker_proposal": obj}

    # start with a clean slate
    AvailabilityModel.objects.filter(**kwargs).delete()

    # all the entered data is in the users local TIME_ZONE, interpret it as such
    tz = ZoneInfo("Europe/Copenhagen")

    # count availability form fields
    fieldcounter = 0
    for field in form.cleaned_data:
        if field[:13] == "availability_":
            fieldcounter += 1

    # loop over form fields, and make sure we get them in sorted order
    formerchunk = None
    fields = list(form.cleaned_data.keys())
    fields.sort()
    for field in fields:
        if field[:13] != "availability_":
            continue

        # this is a speaker_availability field, first split the
        # fieldname to get the tzrange for this daychunk
        elements = field.split("_")
        # format is "availability_2020_08_28_18_00_to_2020_08_28_21_00"
        daychunk = DateTimeTZRange(
            datetime.datetime(
                int(elements[1]),
                int(elements[2]),
                int(elements[3]),
                int(elements[4]),
                int(elements[5]),
            ).replace(tz=tz),
            datetime.datetime(
                int(elements[7]),
                int(elements[8]),
                int(elements[9]),
                int(elements[10]),
                int(elements[11]),
            ).replace(tz=tz),
        )
        available = form.cleaned_data[field]

        if fieldcounter == 1:
            # we only have one field in the form, no field merging to be done
            AvailabilityModel.objects.create(
                when=daychunk,
                available=available,
                **kwargs,
            )
            continue

        # we have more than one form field, but we want to save continuous ranges
        # as one SpeakerAvailability object, so we might need to merge this field with
        # the next one, so we can't save it yet
        if not formerchunk:
            # this is the first loop or we changed availability,
            # remember the current chunk for the next loop
            formerchunk = daychunk
            formeravailable = available
            continue

        # this is not the first chunk
        if formeravailable == available and formerchunk.upper == daychunk.lower:
            # we have the same value for "available" and adjacent times,
            # merge with the former chunk
            formerchunk = formerchunk + daychunk
        else:
            # "available" changed or daychunk is not adjacent to formerchunk
            AvailabilityModel.objects.create(
                when=formerchunk,
                available=formeravailable,
                **kwargs,
            )
            # and remember the current chunk for next iteration
            formerchunk = daychunk
            formeravailable = available

    # save the last chunk?
    if formerchunk:
        AvailabilityModel.objects.create(
            when=formerchunk,
            available=available,
            **kwargs,
        )


def add_existing_availability_to_matrix(matrix, speaker_proposal) -> None:
    """Loops over the matrix and adds an "intial" member to the daychunk dicts
    with the availability info for the speaker_proposal.
    This is used to populate initial form field values and to set <td> background
    colours in the html table.
    speaker_proposal can be either a SpeakerProposal object or a Speaker object.
    """
    # loop over dates in the matrix
    for date in matrix:
        # loop over daychunks and check if we need a checkbox
        for daychunk in matrix[date]:
            if not matrix[date][daychunk]:
                # we have no event_session here, carry on
                continue
            # do we have any availability info for this speakerproposal?
            try:
                availability = speaker_proposal.availabilities.get(
                    when__contains=daychunk,
                )
                matrix[date][daychunk]["initial"] = availability.available
            except ObjectDoesNotExist:
                matrix[date][daychunk]["initial"] = None


def get_slots(period, duration, bounds="()"):
    """Cuts a DateTimeTZRange into slices of duration minutes length and returns a list of them."""
    slots = []
    if period.upper - period.lower < timedelta(minutes=duration):
        # this period is shorter than the duration, no slots
        return slots

    # create the first slot
    slot = DateTimeTZRange(
        period.lower,
        period.lower + timedelta(minutes=duration),
        bounds=bounds,
    )

    # loop until we pass the end
    while slot.upper < period.upper:
        slots.append(slot)
        # the next slot starts when this one ends
        slot = DateTimeTZRange(
            slot.upper,
            slot.upper + timedelta(minutes=duration),
            bounds=bounds,
        )

    # append the final slot to the list unless it continues past the end
    if not slot.upper > period.upper:
        slots.append(slot)
    return slots


def get_tzrange_days(tzranges):
    """Loop over tzranges and build a list of datetimetzranges representing all unique dates (in the local timezone)."""
    days = set()
    # loop over input ranges
    for tzrange in tzranges:
        # convert this range to local timezone
        localrange = DateTimeTZRange(
            timezone.localtime(tzrange.lower),
            timezone.localtime(tzrange.upper),
        )
        # find the first date in this range
        day = DateTimeTZRange(
            localrange.lower.replace(hour=0),
            localrange.lower.replace(hour=0) + timedelta(days=1),
        )
        # add this day to the set
        days.add(day)
        # does this range spans multiple dates?
        if localrange.lower.date() != localrange.upper.date():
            # this range spans multiple dates, loop over them
            while day.lower.date() <= localrange.upper.date():
                day = DateTimeTZRange(day.upper, day.upper + timedelta(days=1))
                days.add(day)
    days = list(days)
    days.sort()
    return days
