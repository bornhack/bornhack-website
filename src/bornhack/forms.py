from __future__ import annotations

from allauth.account.forms import SignupForm
from django import forms
from django.core.exceptions import ValidationError


class AllAuthSignupCaptchaForm(SignupForm):
    """Used with settings.ACCOUNT_FORMS to add a captcha field."""

    first_bornhack_year = forms.CharField(
        initial="",
        help_text="Please help us prevent a few bot signups by telling us the year of the first BornHack. You can find a list of all BornHack events in the <a href='/camps/'>camp list</a>.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            "email"
        ].help_text = "NOTE WELL: Microsoft blocks email from BornHack. If your email ends with @hotmail.com or @outlook.com it is likely we will be unable to send email to you. Please use a different email address."

    def clean_first_bornhack_year(self):
        if self.cleaned_data["first_bornhack_year"] != "2016":
            raise ValidationError("To error is human. Please try to be less human! :)")

    def signup(self, request, user):
        user.save()
