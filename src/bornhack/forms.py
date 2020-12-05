from django import forms
from django.core.exceptions import ValidationError


class AllAuthSignupCaptchaForm(forms.Form):
    first_bornhack_year = forms.CharField(
        initial="",
        help_text="Please help us prevent a few bot signups by telling us the year of the first BornHack.",
    )

    def clean_first_bornhack_year(self):
        if self.cleaned_data["first_bornhack_year"] != "2016":
            raise ValidationError("To error is human. Please try to be less human! :)")

    def signup(self, request, user):
        user.save()
