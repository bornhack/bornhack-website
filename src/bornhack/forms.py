from django import forms
from django.core.exceptions import ValidationError


class AllAuthSignupCaptchaForm(forms.Form):
    """Used with settings.ACCOUNT_SIGNUP_FORM_CLASS to add a captcha field."""
    first_bornhack_year = forms.CharField(
        initial="",
        help_text="Please help us prevent a few bot signups by telling us the year of the first BornHack. You can find a list of all BornHack events in the <a href='/camps/'>camp list</a>.",
    )

    def clean_first_bornhack_year(self):
        if self.cleaned_data["first_bornhack_year"] != "2016":
            raise ValidationError("To error is human. Please try to be less human! :)")

    def signup(self, request, user):
        user.save()
