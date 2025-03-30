"""Custom OAuth2Validator subclass."""

from oauth2_provider.oauth2_validators import OAuth2Validator


class BornhackOAuth2Validator(OAuth2Validator):
    """Claims and scopes."""

    # scopes required for custom claims
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope
    oidc_claim_scope.update(
        {
            "profile": "profile:read",
            "user": "profile:read",
            "teams": "profile:read",
        }
    )

    def get_claim_dict(self, request) -> dict[str, str]:
        """Return username (usually a uuid) instead of user pk in the 'sub' claim."""
        return {
            "sub": request.user.username,
            **self.get_additional_claims(request=request),
        }

    def get_additional_claims(self, request) -> dict[str, str | list[dict[str, str]]]:
        """
        Define the custom oidc claims to support, and how to get the data.

        https://django-oauth-toolkit.readthedocs.io/en/latest/oidc.html#using-oidc-scopes-to-determine-which-claims-are-returned
        """
        claims = {
            "user": {
                "username": request.user.username,
                "user_id": request.user.id,
            },
        }

        # is there a real user behind this request?
        if request.user.is_anonymous:
            claims.update(
                {
                    "profile": {
                        "public_credit_name": "Anonymous User",
                        "description": "",
                    },
                    "teams": [],
                },
            )
        else:
            claims.update(
                {
                    "profile": {
                        "public_credit_name": request.user.profile.get_public_credit_name,
                        "description": request.user.profile.description,
                    },
                    "teams": [
                        {"team": team.name, "camp": team.camp.title}
                        for team in request.user.teams.all()
                    ],
                },
            )
        return claims

    def get_discovery_claims(self, request) -> list[str]:
        """Make oidc claims discoverable.

        https://django-oauth-toolkit.readthedocs.io/en/latest/oidc.html#supported-claims-discovery
        """
        return self.get_claim_dict(request=request).keys()
