from __future__ import annotations

from django import forms


class TokenFindSubmitForm(forms.Form):
    """Form definition for TokenFindSubmitForm."""

    token = forms.CharField()
