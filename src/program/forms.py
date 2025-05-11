import logging

from django import forms
from django.core.exceptions import ImproperlyConfigured

from utils.widgets import MarkdownWidget

from .models import Event
from .models import EventProposal
from .models import EventTrack
from .models import SpeakerProposal

logger = logging.getLogger("bornhack.%s" % __name__)


class SpeakerProposalForm(forms.ModelForm):
    """The SpeakerProposalForm. Takes a list of EventTypes in __init__,
    and changes fields accordingly if the list has 1 element.
    """

    class Meta:
        model = SpeakerProposal
        fields = [
            "name",
            "email",
            "biography",
            "needs_oneday_ticket",
            "submission_notes",
            "event_conflicts",
        ]

    def __init__(self, camp, event_type=None, matrix=None, *args, **kwargs):
        """Initialise the form and adapt based on event_type"""
        super().__init__(*args, **kwargs)

        matrix = matrix or {}

        # only show events from this camp
        self.fields["event_conflicts"].queryset = Event.objects.filter(
            track__camp=camp,
            event_type__support_speaker_event_conflicts=True,
        )

        if matrix:
            # add speaker availability fields
            for date in matrix.keys():
                # do we need a column for this day?
                if matrix[date]:
                    # loop over the daychunks for this day
                    for daychunk in matrix[date]:
                        if matrix[date][daychunk]:
                            # add the field
                            self.fields[matrix[date][daychunk]["fieldname"]] = forms.BooleanField(required=False)
                            # add it to Meta.fields too
                            self.Meta.fields.append(matrix[date][daychunk]["fieldname"])

        # adapt form based on EventType?
        if not event_type:
            # we have no event_type to customize the form, use the default form
            return

        if event_type.name == "Debate":
            # fix label and help_text for the name field
            self.fields["name"].label = "Guest Name"
            self.fields["name"].help_text = "The name of a debate guest. Can be a real name or an alias (public)."

            # fix label and help_text for the email field
            self.fields["email"].label = "Guest Email"
            self.fields[
                "email"
            ].help_text = (
                "The email for this guest. Will default to the logged-in users email if left empty (not public)."
            )

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Guest Biography"
            self.fields["biography"].help_text = "The biography of the guest (public)."
            self.fields["biography"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].help_text = "Private notes regarding this guest (not public)."

            # no free tickets for debates
            del self.fields["needs_oneday_ticket"]

        elif event_type.name == "Lightning Talk":
            # fix label and help_text for the name field
            self.fields["name"].label = "Speaker Name"
            self.fields["name"].help_text = "The name of the speaker. Can be a real name or an alias (public)."

            # fix label and help_text for the email field
            self.fields["email"].label = "Speaker Email"
            self.fields[
                "email"
            ].help_text = (
                "The email for this speaker. Will default to the logged-in users email if left empty. (not public)"
            )

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Speaker Biography"
            self.fields["biography"].help_text = "The biography of the speaker (public)"
            self.fields["biography"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].help_text = "Private notes regarding this speaker (not public)."

            # no free tickets for lightning talks
            del self.fields["needs_oneday_ticket"]

        elif event_type.name == "Music Act":
            # fix label and help_text for the name field
            self.fields["name"].label = "Artist Name"
            self.fields["name"].help_text = "The name of the artist. Can be a real name or artist alias (public)."

            # fix label and help_text for the email field
            self.fields["email"].label = "Artist Email"
            self.fields[
                "email"
            ].help_text = (
                "The email for this artist. Will default to the logged-in users email if left empty (not public)."
            )

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Artist Description"
            self.fields["biography"].help_text = "The description of the artist (public)."
            self.fields["biography"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].help_text = "Private notes regarding this artist (not public)."

            # no oneday tickets for music acts
            del self.fields["needs_oneday_ticket"]

        elif event_type.name == "Talk" or event_type.name == "Keynote":
            # fix label and help_text for the name field
            self.fields["name"].label = "Speaker Name"
            self.fields["name"].help_text = "The name of the speaker. Can be a real name or an alias (public)."

            # fix label and help_text for the email field
            self.fields["email"].label = "Speaker Email"
            self.fields[
                "email"
            ].help_text = (
                "The email for this speaker. Will default to the logged-in users email if left empty (not public)."
            )

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Speaker Biography"
            self.fields["biography"].help_text = "The biography of the speaker (public)."
            self.fields["biography"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].help_text = "Private notes regarding this speaker (not public)"

        elif event_type.name == "Workshop":
            # fix label and help_text for the name field
            self.fields["name"].label = "Host Name"
            self.fields["name"].help_text = "The name of the workshop host. Can be a real name or an alias (public)."

            # fix label and help_text for the email field
            self.fields["email"].label = "Host Email"
            self.fields[
                "email"
            ].help_text = (
                "The email for the host. Will default to the logged-in users email if left empty (not public)."
            )

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Host Biography"
            self.fields["biography"].help_text = "The biography of the host (public)."
            self.fields["biography"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].help_text = "Private notes regarding this host (not public)."

            # no free tickets for workshops
            del self.fields["needs_oneday_ticket"]

        elif event_type.name == "Recreational Event":
            # fix label and help_text for the name field
            self.fields["name"].label = "Host Name"
            self.fields["name"].help_text = "Can be a real name or an alias (public)."

            # fix label and help_text for the email field
            self.fields["email"].label = "Host Email"
            self.fields[
                "email"
            ].help_text = (
                "The email for the host. Will default to the logged-in users email if left empty (not public)."
            )

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Host Biography"
            self.fields["biography"].help_text = "The biography of the host (public)."
            self.fields["biography"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].help_text = "Private notes regarding this host (not public)."

            # no free tickets for recreational events
            del self.fields["needs_oneday_ticket"]

        elif event_type.name == "Meetup":
            # fix label and help_text for the name field
            self.fields["name"].label = "Host Name"
            self.fields["name"].help_text = "The name of the meetup host. Can be a real name or an alias (public)."

            # fix label and help_text for the email field
            self.fields["email"].label = "Host Email"
            self.fields[
                "email"
            ].help_text = (
                "The email for the host. Will default to the logged-in users email if left empty (not public)."
            )

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Host Biography"
            self.fields["biography"].help_text = "The biography of the host."
            self.fields["biography"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].help_text = "Private notes regarding this host (not public)."

            # no free tickets for meetups
            del self.fields["needs_oneday_ticket"]

        else:
            raise ImproperlyConfigured(
                f"Unsupported event type '{event_type.name}', don't know which form class to use",
            )


class EventProposalForm(forms.ModelForm):
    """The EventProposalForm. Takes an EventType in __init__ and changes fields accordingly."""

    slides_url = forms.URLField(
        label="Slides URL",
        help_text="Add a URL to your slides.",
        required=False,
    )

    class Meta:
        model = EventProposal
        fields = [
            "title",
            "abstract",
            "allow_video_recording",
            "allow_video_streaming",
            "duration",
            "tags",
            "slides_url",
            "submission_notes",
            "track",
            "use_provided_speaker_laptop",
        ]

    def clean_duration(self):
        """Make sure duration has been specified, and make sure it is not too long"""
        if not self.cleaned_data["duration"]:
            raise forms.ValidationError("Please specify a duration.")
        if (
            self.event_type.event_duration_minutes
            and self.cleaned_data["duration"] > self.event_type.event_duration_minutes
        ):
            raise forms.ValidationError(
                f"Please keep duration under {self.event_type.event_duration_minutes} minutes.",
            )
        return self.cleaned_data["duration"]

    def clean_track(self):
        track = self.cleaned_data["track"]
        # TODO: make sure the track is part of the current camp, needs camp as form kwarg to verify
        return track

    def __init__(self, camp, event_type=None, matrix=None, *args, **kwargs):
        # initialise form
        super().__init__(*args, **kwargs)

        # we need event_type for cleaning later
        self.event_type = event_type

        TALK = "Talk"
        LIGHTNING_TALK = "Lightning Talk"
        DEBATE = "Debate"
        MUSIC_ACT = "Music Act"
        RECREATIONAL_EVENT = "Recreational Event"
        WORKSHOP = "Workshop"
        MEETUP = "Meetup"

        # disable the empty_label for the track select box
        self.fields["track"].empty_label = None
        self.fields["track"].queryset = EventTrack.objects.filter(camp=camp)

        # make sure video_recording and streaming checkbox defaults to checked
        self.fields["allow_video_recording"].initial = True
        self.fields["allow_video_streaming"].initial = True

        if event_type.name not in [TALK, LIGHTNING_TALK]:
            # Only talk or lightning talk should show the slides_url field
            del self.fields["slides_url"]

        # better placeholder text for duration field
        self.fields["duration"].label = f"{event_type.name} Duration"
        self.fields["submission_notes"].label = "Notes to the Content Team"
        if event_type.event_duration_minutes:
            self.fields[
                "duration"
            ].help_text = f"Please enter the duration of this {event_type.name} (in minutes, max {event_type.event_duration_minutes})"
            self.fields["duration"].widget.attrs["placeholder"] = (
                f"{event_type.name} Duration (in minutes, max {event_type.event_duration_minutes})"
            )
        else:
            self.fields["duration"].help_text = f"Please enter the duration of this {event_type.name} (in minutes)"
            self.fields["duration"].widget.attrs["placeholder"] = f"{event_type.name} Duration (in minutes)"

        if not event_type.name == LIGHTNING_TALK:
            # Only lightning talks submissions will have to choose whether to use provided speaker laptop
            del self.fields["use_provided_speaker_laptop"]

        if event_type.name == DEBATE:
            # fix label and help_text for the title field
            self.fields["title"].label = "Title of debate"
            self.fields["title"].help_text = "The title of this debate"

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Description"
            self.fields["abstract"].help_text = "The description of this debate"
            self.fields["abstract"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this debate. Only visible to yourself and the BornHack organisers."

        elif event_type.name == MUSIC_ACT:
            # fix label and help_text for the title field
            self.fields["title"].label = "Title of music act"
            self.fields["title"].help_text = "The title of this music act/concert/set."

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Description"
            self.fields["abstract"].help_text = "The description of this music act"
            self.fields["abstract"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields[
                "submission_notes"
            ].help_text = (
                "Private notes regarding this music act. Only visible to yourself and the BornHack organisers."
            )

            # no video recording for music acts
            del self.fields["allow_video_recording"]
            del self.fields["allow_video_streaming"]

        elif event_type.name == RECREATIONAL_EVENT:
            # fix label and help_text for the title field
            self.fields["title"].label = "Event Title"
            self.fields["title"].help_text = "The title of this recreational event"

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Event Abstract"
            self.fields["abstract"].help_text = "The description/abstract of this recreational event."
            self.fields["abstract"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields[
                "submission_notes"
            ].help_text = (
                "Private notes regarding this recreational event. Only visible to yourself and the BornHack organisers."
            )

            # no video recording for music acts
            del self.fields["allow_video_recording"]
            del self.fields["allow_video_streaming"]

        elif event_type.name in [TALK, LIGHTNING_TALK]:
            # fix label and help_text for the title field
            self.fields["title"].label = "Title of Talk"
            self.fields["title"].help_text = "The title of this talk/presentation."

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Abstract of Talk"
            self.fields[
                "abstract"
            ].help_text = (
                "The description/abstract of this talk/presentation. Explain what the audience will experience."
            )
            self.fields["abstract"].widget = MarkdownWidget()

            # fix label and help_text for the submission_notes field
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this talk. Only visible to yourself and the BornHack organisers."

            if self.fields.get("slides_url") and event_type.name == LIGHTNING_TALK:
                self.fields[
                    "slides_url"
                ].help_text += " You will only get assigned a slot if you have provided slides (a title slide is enough if you don't use slides for the talk). You can add an URL later if need be."

            # no duration for talks
            del self.fields["duration"]

        elif event_type.name == WORKSHOP:
            # fix label and help_text for the title field
            self.fields["title"].label = "Workshop Title"
            self.fields["title"].help_text = "The title of this workshop."

            # fix label and help_text for the submission_notes field
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this workshop. Only visible to yourself and the BornHack organisers."

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Workshop Abstract"
            self.fields[
                "abstract"
            ].help_text = "The description/abstract of this workshop. Explain what the participants will learn."
            self.fields["abstract"].widget = MarkdownWidget()

            # no video recording for workshops
            del self.fields["allow_video_recording"]
            del self.fields["allow_video_streaming"]

        elif event_type.name == RECREATIONAL_EVENT:
            # fix label and help_text for the title field
            self.fields["title"].label = "Event Title"
            self.fields["title"].help_text = "The title of this recreational event."

            # fix label and help_text for the submission_notes field
            self.fields[
                "submission_notes"
            ].help_text = (
                "Private notes regarding this recreational event. Only visible to yourself and the BornHack organisers."
            )

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Event Abstract"
            self.fields[
                "abstract"
            ].help_text = "The description/abstract of this event. Explain what the participants will experience."
            self.fields["abstract"].widget = MarkdownWidget()

            # no video recording for recreational events
            del self.fields["allow_video_recording"]
            del self.fields["allow_video_streaming"]

        elif event_type.name == MEETUP:
            # fix label and help_text for the title field
            self.fields["title"].label = "Meetup Title"
            self.fields["title"].help_text = "The title of this meetup."

            # fix label and help_text for the submission_notes field
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this meetup. Only visible to yourself and the BornHack organisers."

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Meetup Abstract"
            self.fields[
                "abstract"
            ].help_text = (
                "The description/abstract of this meetup. Explain what the meetup is about and who should attend."
            )
            self.fields["abstract"].widget = MarkdownWidget()

            # no video recording for meetups
            del self.fields["allow_video_recording"]
            del self.fields["allow_video_streaming"]

        else:
            raise ImproperlyConfigured(
                "Unsupported event type, don't know which form class to use",
            )
