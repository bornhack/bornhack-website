from django.forms import ModelForm
from .models import Team


class ManageTeamForm(ModelForm):
    class Meta:
        model = Team
        fields = ['description', 'needs_members']
