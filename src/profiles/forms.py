from django import forms

from . import models


class ProfileForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = models.Profile
        fields = []
