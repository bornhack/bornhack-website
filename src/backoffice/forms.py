from django import forms
from program.models import Event


class AddRecordingForm(forms.ModelForm):
    recording_url = forms.URLField(
        label="Recording URL", help_text="Add a URL to the recording.", required=False
    )

    class Meta:
        model = Event
        fields = ["video_recording","recording_url"]


