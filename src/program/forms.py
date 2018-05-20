from django import forms
from betterforms.multiform import MultiModelForm
from collections import OrderedDict
from .models import SpeakerProposal, EventProposal, EventTrack
from django.forms.widgets import TextInput
from django.utils.dateparse import parse_duration
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class BaseSpeakerProposalForm(forms.ModelForm):
    """
    The BaseSpeakerProposalForm is not used directly.
    It is subclassed for each eventtype, where fields are removed or get new labels and help_text as needed
    """
    class Meta:
        model = SpeakerProposal
        fields = ['name', 'biography', 'needs_oneday_ticket', 'submission_notes']


class BaseEventProposalForm(forms.ModelForm):
    """
    The BaseEventProposalForm is not used directly.
    It is subclassed for each eventtype, where fields are removed or get new labels and help_text as needed
    """
    class Meta:
        model = EventProposal
        fields = ['title', 'abstract', 'allow_video_recording', 'duration', 'submission_notes', 'track']

    def clean_duration(self):
        duration = self.cleaned_data['duration']
        if duration < 60 or duration > 180:
            raise forms.ValidationError("Please keep duration between 60 and 180 minutes.")
        return duration

    def clean_track(self):
        track = self.cleaned_data['track']
        # TODO: make sure the track is part of the current camp, needs camp as form kwarg to verify
        return track

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # disable the empty_label for the track select box
        self.fields['track'].empty_label = None


################################ EventType "Talk" ################################################


class TalkEventProposalForm(BaseEventProposalForm):
    """
    EventProposalForm with field names and help_text adapted to talk submissions
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # fix label and help_text for the title field
        self.fields['title'].label = 'Title of Talk'
        self.fields['title'].help_text = 'The title of this talk/presentation.'

        # fix label and help_text for the abstract field
        self.fields['abstract'].label = 'Abstract of Talk'
        self.fields['abstract'].help_text = 'The description/abstract of this talk/presentation. Explain what the audience will experience.'

        # fix label and help_text for the submission_notes field
        self.fields['submission_notes'].label = 'Talk Notes'
        self.fields['submission_notes'].help_text = 'Private notes regarding this talk. Only visible to yourself and the BornHack organisers.'

        # no duration for talks
        del(self.fields['duration'])


class TalkSpeakerProposalForm(BaseSpeakerProposalForm):
    """
    SpeakerProposalForm with field labels and help_text adapted for talk submissions
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # fix label and help_text for the name field
        self.fields['name'].label = 'Speaker Name'
        self.fields['name'].help_text = 'The name of the speaker. Can be a real name or an alias.'

        # fix label and help_text for the biograpy field
        self.fields['biography'].label = 'Speaker Biography'
        self.fields['biography'].help_text = 'The biography of the speaker.'

        # fix label and help_text for the submission_notes field
        self.fields['submission_notes'].label = 'Speaker Notes'
        self.fields['submission_notes'].help_text = 'Private notes regarding this speaker. Only visible to yourself and the BornHack organisers.'


################################ EventType "Lightning Talk" ################################################


class LightningTalkEventProposalForm(TalkEventProposalForm):
    """
    LightningTalkEventProposalForm is identical to TalkEventProposalForm for now. Keeping the class here for easy customisation later.
    """
    pass

class LightningTalkSpeakerProposalForm(TalkSpeakerProposalForm):
    """
    LightningTalkSpeakerProposalForm is identical to TalkSpeakerProposalForm except for no free tickets
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # no free tickets for lightning talks
        del(self.fields['needs_oneday_ticket'])


################################ EventType "Workshop" ################################################


class WorkshopEventProposalForm(BaseEventProposalForm):
    """
    EventProposalForm with field names and help_text adapted for workshop submissions
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # fix label and help_text for the title field
        self.fields['title'].label = 'Workshop Title'
        self.fields['title'].help_text = 'The title of this workshop.'

        # fix label and help_text for the submission_notes field
        self.fields['submission_notes'].label = 'Workshop Notes'
        self.fields['submission_notes'].help_text = 'Private notes regarding this workshop. Only visible to yourself and the BornHack organisers.'

        # fix label and help_text for the abstract field
        self.fields['abstract'].label = 'Workshop Abstract'
        self.fields['abstract'].help_text = 'The description/abstract of this workshop. Explain what the participants will learn.'

        # no video recording for workshops
        del(self.fields['allow_video_recording'])

        # duration field
        self.fields['duration'].label = 'Workshop Duration'
        self.fields['duration'].help_text = 'How much time (in minutes) should we set aside for this workshop? Please keep it between 60 and 180 minutes (1-3 hours).'

class WorkshopSpeakerProposalForm(BaseSpeakerProposalForm):
    """
    SpeakerProposalForm with field labels and help_text adapted for workshop submissions
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # fix label and help_text for the name field
        self.fields['name'].label = 'Host Name'
        self.fields['name'].help_text = 'The name of the workshop host. Can be a real name or an alias.'

        # fix label and help_text for the biograpy field
        self.fields['biography'].label = 'Host Biography'
        self.fields['biography'].help_text = 'The biography of the host.'

        # fix label and help_text for the submission_notes field
        self.fields['submission_notes'].label = 'Host Notes'
        self.fields['submission_notes'].help_text = 'Private notes regarding this host. Only visible to yourself and the BornHack organisers.'

        # no free tickets for workshops
        del(self.fields['needs_oneday_ticket'])


################################ EventType "Music" ################################################


class MusicEventProposalForm(BaseEventProposalForm):
    """
    EventProposalForm with field names and help_text adapted to music submissions
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # fix label and help_text for the title field
        self.fields['title'].label = 'Title of music act'
        self.fields['title'].help_text = 'The title of this music act/concert/set.'

        # fix label and help_text for the submission_notes field
        self.fields['submission_notes'].label = 'Music Act Notes'
        self.fields['submission_notes'].help_text = 'Private notes regarding this music act. Only visible to yourself and the BornHack organisers.'

        # no video recording for music acts
        del(self.fields['allow_video_recording'])

        # no abstract for music acts
        del(self.fields['abstract'])

        # better placeholder text for duration field
        self.fields['duration'].widget.attrs['placeholder'] = 'Duration (minutes)'


class MusicSpeakerProposalForm(BaseSpeakerProposalForm):
    """
    SpeakerProposalForm with field labels and help_text adapted for music submissions
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # fix label and help_text for the name field
        self.fields['name'].label = 'Artist Name'
        self.fields['name'].help_text = 'The name of the artist. Can be a real name or artist alias.'

        # fix label and help_text for the biograpy field
        self.fields['biography'].label = 'Artist Description'
        self.fields['biography'].help_text = 'The description of the artist.'

        # fix label and help_text for the submission_notes field
        self.fields['submission_notes'].label = 'Artist Notes'
        self.fields['submission_notes'].help_text = 'Private notes regarding this artist. Only visible to yourself and the BornHack organisers.'

        # no oneday tickets for music acts
        del(self.fields['needs_oneday_ticket'])


################################ EventType "Slacking Off" ################################################


class SlackEventProposalForm(BaseEventProposalForm):
    """
    EventProposalForm with field names and help_text adapted to slacking off submissions
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # fix label and help_text for the title field
        self.fields['title'].label = 'Event Title'
        self.fields['title'].help_text = 'The title of this recreational event'

        # fix label and help_text for the abstract field
        self.fields['abstract'].label = 'Event Abstract'
        self.fields['abstract'].help_text = 'The description/abstract of this recreational event.'

        # fix label and help_text for the submission_notes field
        self.fields['submission_notes'].label = 'Event Notes'
        self.fields['submission_notes'].help_text = 'Private notes regarding this recreational event. Only visible to yourself and the BornHack organisers.'

        # no video recording for music acts
        del(self.fields['allow_video_recording'])

        # better placeholder text for duration field
        self.fields['duration'].label = 'Event Duration'
        self.fields['duration'].widget.attrs['placeholder'] = 'Duration (minutes)'


class SlackSpeakerProposalForm(BaseSpeakerProposalForm):
    """
    SpeakerProposalForm with field labels and help_text adapted for recreational events
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # fix label and help_text for the name field
        self.fields['name'].label = 'Host Name'
        self.fields['name'].help_text = 'The name of the event host. Can be a real name or an alias.'

        # fix label and help_text for the biograpy field
        self.fields['biography'].label = 'Host Biography'
        self.fields['biography'].help_text = 'The biography of the host.'

        # fix label and help_text for the submission_notes field
        self.fields['submission_notes'].label = 'Host Notes'
        self.fields['submission_notes'].help_text = 'Private notes regarding this host. Only visible to yourself and the BornHack organisers.'

        # no oneday tickets for music acts
        del(self.fields['needs_oneday_ticket'])

