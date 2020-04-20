import logging

from django import forms
from django.core.exceptions import ImproperlyConfigured

from .models import Event, EventProposal, EventTrack, SpeakerProposal, Url, UrlType

logger = logging.getLogger("bornhack.%s" % __name__)


class SpeakerProposalForm(forms.ModelForm):
    """
    The SpeakerProposalForm. Takes a list of EventTypes in __init__,
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

    def __init__(self, camp, event_type=None, matrix={}, *args, **kwargs):
        """
        initialise the form and adapt based on event_type
        """
        super().__init__(*args, **kwargs)

        # only show events from this camp
        self.fields["event_conflicts"].queryset = Event.objects.filter(
            track__camp=camp, event_type__support_speaker_event_conflicts=True,
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
                            self.fields[
                                matrix[date][daychunk]["fieldname"]
                            ] = forms.BooleanField(required=False)
                            # add it to Meta.fields too
                            self.Meta.fields.append(matrix[date][daychunk]["fieldname"])

        # adapt form based on EventType?
        if not event_type:
            # we have no event_type to customize the form, use the default form
            return

        if event_type.name == "Debate":
            # fix label and help_text for the name field
            self.fields["name"].label = "Guest Name"
            self.fields[
                "name"
            ].help_text = "The name of a debate guest. Can be a real name or an alias."

            # fix label and help_text for the email field
            self.fields["email"].label = "Guest Email"
            self.fields[
                "email"
            ].help_text = "The email for this guest. Will default to the logged-in users email if left empty."

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Guest Biography"
            self.fields["biography"].help_text = "The biography of the guest."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Guest Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this guest. Only visible to yourself and the BornHack organisers."

            # no free tickets for debates
            del self.fields["needs_oneday_ticket"]

        elif event_type.name == "Lightning Talk":
            # fix label and help_text for the name field
            self.fields["name"].label = "Speaker Name"
            self.fields[
                "name"
            ].help_text = "The name of the speaker. Can be a real name or an alias."

            # fix label and help_text for the email field
            self.fields["email"].label = "Speaker Email"
            self.fields[
                "email"
            ].help_text = "The email for this speaker. Will default to the logged-in users email if left empty."

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Speaker Biography"
            self.fields["biography"].help_text = "The biography of the speaker."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Speaker Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this speaker. Only visible to yourself and the BornHack organisers."

            # no free tickets for lightning talks
            del self.fields["needs_oneday_ticket"]

        elif event_type.name == "Music Act":
            # fix label and help_text for the name field
            self.fields["name"].label = "Artist Name"
            self.fields[
                "name"
            ].help_text = "The name of the artist. Can be a real name or artist alias."

            # fix label and help_text for the email field
            self.fields["email"].label = "Artist Email"
            self.fields[
                "email"
            ].help_text = "The email for this artist. Will default to the logged-in users email if left empty."

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Artist Description"
            self.fields["biography"].help_text = "The description of the artist."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Artist Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this artist. Only visible to yourself and the BornHack organisers."

            # no oneday tickets for music acts
            del self.fields["needs_oneday_ticket"]

        elif event_type.name == "Talk":
            # fix label and help_text for the name field
            self.fields["name"].label = "Speaker Name"
            self.fields[
                "name"
            ].help_text = "The name of the speaker. Can be a real name or an alias."

            # fix label and help_text for the email field
            self.fields["email"].label = "Speaker Email"
            self.fields[
                "email"
            ].help_text = "The email for this speaker. Will default to the logged-in users email if left empty."

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Speaker Biography"
            self.fields["biography"].help_text = "The biography of the speaker."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Speaker Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this speaker. Only visible to yourself and the BornHack organisers."

        elif event_type.name == "Workshop":
            # fix label and help_text for the name field
            self.fields["name"].label = "Host Name"
            self.fields[
                "name"
            ].help_text = (
                "The name of the workshop host. Can be a real name or an alias."
            )

            # fix label and help_text for the email field
            self.fields["email"].label = "Host Email"
            self.fields[
                "email"
            ].help_text = "The email for the host. Will default to the logged-in users email if left empty."

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Host Biography"
            self.fields["biography"].help_text = "The biography of the host."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Host Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this host. Only visible to yourself and the BornHack organisers."

            # no free tickets for workshops
            del self.fields["needs_oneday_ticket"]

        elif event_type.name == "Recreational Event":
            # fix label and help_text for the name field
            self.fields["name"].label = "Host Name"
            self.fields["name"].help_text = "Can be a real name or an alias."

            # fix label and help_text for the email field
            self.fields["email"].label = "Host Email"
            self.fields[
                "email"
            ].help_text = "The email for the host. Will default to the logged-in users email if left empty."

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Host Biography"
            self.fields["biography"].help_text = "The biography of the host."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Host Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this host. Only visible to yourself and the BornHack organisers."

            # no free tickets for recreational events
            del self.fields["needs_oneday_ticket"]

        elif event_type.name == "Meetup":
            # fix label and help_text for the name field
            self.fields["name"].label = "Host Name"
            self.fields[
                "name"
            ].help_text = "The name of the meetup host. Can be a real name or an alias."

            # fix label and help_text for the email field
            self.fields["email"].label = "Host Email"
            self.fields[
                "email"
            ].help_text = "The email for the host. Will default to the logged-in users email if left empty."

            # fix label and help_text for the biograpy field
            self.fields["biography"].label = "Host Biography"
            self.fields["biography"].help_text = "The biography of the host."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Host Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this host. Only visible to yourself and the BornHack organisers."

            # no free tickets for meetups
            del self.fields["needs_oneday_ticket"]

        else:
            raise ImproperlyConfigured(
                "Unsupported event type, don't know which form class to use"
            )


class EventProposalForm(forms.ModelForm):
    """
    The EventProposalForm. Takes an EventType in __init__ and changes fields accordingly.
    """

    slides_url = forms.URLField(
        label="Slides URL", help_text="Add a URL to your slides.", required=False
    )

    class Meta:
        model = EventProposal
        fields = [
            "title",
            "abstract",
            "allow_video_recording",
            "duration",
            "slides_url",
            "submission_notes",
            "track",
            "use_provided_speaker_laptop",
        ]

    def clean_duration(self):
        duration = self.cleaned_data["duration"]
        if not duration or duration < 60 or duration > 180:
            raise forms.ValidationError(
                "Please keep duration between 60 and 180 minutes."
            )
        return duration

    def clean_track(self):
        track = self.cleaned_data["track"]
        # TODO: make sure the track is part of the current camp, needs camp as form kwarg to verify
        return track

    def save(self, commit=True, user=None, event_type=None):
        event_proposal = super().save(commit=False)
        if user:
            event_proposal.user = user
        if event_type:
            event_proposal.event_type = event_type
        event_proposal.save()

        if not event_type and hasattr(event_proposal, "event_type"):
            event_type = event_proposal.event_type

        if self.cleaned_data.get("slides_url") and event_type.name in [
            "Talk",
            "Lightning Talk",
        ]:
            url = self.cleaned_data.get("slides_url")
            if not event_proposal.urls.filter(url=url).exists():
                slides_url = Url()
                slides_url.event_proposal = event_proposal
                slides_url.url = url
                slides_url.url_type = UrlType.objects.get(name="Slides")
                slides_url.save()

        return event_proposal

    def __init__(self, camp, event_type=None, matrix=None, *args, **kwargs):
        # initialise form
        super().__init__(*args, **kwargs)

        TALK = "Talk"
        LIGHTNING_TALK = "Lightning Talk"
        DEBATE = "Debate"
        MUSIC_ACT = "Music Act"
        RECREATIONAL_EVENT = "Recreational Event"
        WORKSHOP = "Workshop"
        SLACKING_OFF = "Slacking Off"
        MEETUP = "Meetup"

        # disable the empty_label for the track select box
        self.fields["track"].empty_label = None
        self.fields["track"].queryset = EventTrack.objects.filter(camp=camp)

        # make sure video_recording checkbox defaults to checked
        self.fields["allow_video_recording"].initial = True

        if event_type.name not in [TALK, LIGHTNING_TALK]:
            # Only talk or lightning talk should show the slides_url field
            del self.fields["slides_url"]

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

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Debate Act Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this debate. Only visible to yourself and the BornHack organisers."

            # better placeholder text for duration field
            self.fields["duration"].widget.attrs[
                "placeholder"
            ] = "Debate Duration (minutes)"

        elif event_type.name == MUSIC_ACT:
            # fix label and help_text for the title field
            self.fields["title"].label = "Title of music act"
            self.fields["title"].help_text = "The title of this music act/concert/set."

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Description"
            self.fields["abstract"].help_text = "The description of this music act"

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Music Act Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this music act. Only visible to yourself and the BornHack organisers."

            # no video recording for music acts
            del self.fields["allow_video_recording"]

            # better placeholder text for duration field
            self.fields["duration"].widget.attrs["placeholder"] = "Duration (minutes)"

        elif event_type.name == RECREATIONAL_EVENT:
            # fix label and help_text for the title field
            self.fields["title"].label = "Event Title"
            self.fields["title"].help_text = "The title of this recreational event"

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Event Abstract"
            self.fields[
                "abstract"
            ].help_text = "The description/abstract of this recreational event."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Event Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this recreational event. Only visible to yourself and the BornHack organisers."

            # no video recording for music acts
            del self.fields["allow_video_recording"]

            # better placeholder text for duration field
            self.fields["duration"].label = "Event Duration"
            self.fields["duration"].widget.attrs["placeholder"] = "Duration (minutes)"

        elif event_type.name in [TALK, LIGHTNING_TALK]:
            # fix label and help_text for the title field
            self.fields["title"].label = "Title of Talk"
            self.fields["title"].help_text = "The title of this talk/presentation."

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Abstract of Talk"
            self.fields[
                "abstract"
            ].help_text = "The description/abstract of this talk/presentation. Explain what the audience will experience."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Talk Notes"
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
            self.fields["submission_notes"].label = "Workshop Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this workshop. Only visible to yourself and the BornHack organisers."

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Workshop Abstract"
            self.fields[
                "abstract"
            ].help_text = "The description/abstract of this workshop. Explain what the participants will learn."

            # no video recording for workshops
            del self.fields["allow_video_recording"]

            # duration field
            self.fields["duration"].label = "Workshop Duration"
            self.fields[
                "duration"
            ].help_text = "How much time (in minutes) should we set aside for this workshop? Please keep it between 60 and 180 minutes (1-3 hours)."

        elif event_type.name == SLACKING_OFF:
            # fix label and help_text for the title field
            self.fields["title"].label = "Event Title"
            self.fields["title"].help_text = "The title of this recreational event."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Event Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this recreational event. Only visible to yourself and the BornHack organisers."

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Event Abstract"
            self.fields[
                "abstract"
            ].help_text = "The description/abstract of this event. Explain what the participants will experience."

            # no video recording for recreational events
            del self.fields["allow_video_recording"]

            # duration field
            self.fields["duration"].label = "Event Duration"
            self.fields[
                "duration"
            ].help_text = "How much time (in minutes) should we set aside for this event? Please keep it between 60 and 180 minutes (1-3 hours)."

        elif event_type.name == MEETUP:
            # fix label and help_text for the title field
            self.fields["title"].label = "Meetup Title"
            self.fields["title"].help_text = "The title of this meetup."

            # fix label and help_text for the submission_notes field
            self.fields["submission_notes"].label = "Meetup Notes"
            self.fields[
                "submission_notes"
            ].help_text = "Private notes regarding this meetup. Only visible to yourself and the BornHack organisers."

            # fix label and help_text for the abstract field
            self.fields["abstract"].label = "Meetup Abstract"
            self.fields[
                "abstract"
            ].help_text = "The description/abstract of this meetup. Explain what the meetup is about and who should attend."

            # no video recording for meetups
            del self.fields["allow_video_recording"]

            # duration field
            self.fields["duration"].label = "Meetup Duration"
            self.fields[
                "duration"
            ].help_text = "How much time (in minutes) should we set aside for this meetup? Please keep it between 60 and 180 minutes (1-3 hours)."

        else:
            raise ImproperlyConfigured(
                "Unsupported event type, don't know which form class to use"
            )
