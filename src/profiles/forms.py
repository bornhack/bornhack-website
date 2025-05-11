from django import forms

from bornhack.oauth_validators import BornhackOAuth2Validator


def get_scopes() -> list[str]:
    validator = BornhackOAuth2Validator()
    return ((scope, scope) for scope in sorted(set(validator.oidc_claim_scope.values())) if scope != "openid")


class OIDCForm(forms.Form):
    scopes = forms.MultipleChoiceField(
        choices=get_scopes,
        help_text="Select the scopes to simulate. The 'openid' scope is always included.",
    )
