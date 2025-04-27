"""Custom OAuth2Validator subclass."""

from oauth2_provider.oauth2_validators import OAuth2Validator


class BornhackOAuth2Validator(OAuth2Validator):
    """Custom OAuth2Validator subclass."""

    # supported user claims and the scopes they require
    # https://django-oauth-toolkit.readthedocs.io/en/latest/oidc.html#using-oidc-scopes-to-determine-which-claims-are-returned
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope
    oidc_claim_scope.update(
        {
            # the OIDC standard user claims we support, and the OIDC standard scopes they require
            "address": "address",
            "email": "email",
            "email_verified": "email",
            "phone_number": "phone",
            "phone_number_verified": "phone",
            "updated_at": "profile",
            # the custom user claims we support, and the (mostly custom) scopes they require
            "bornhack:v2:description": "profile",
            "bornhack:v2:groups": "groups:read",
            "bornhack:v2:permissions": "permissions:read",
            "bornhack:v2:public_credit_name": "profile",
            "bornhack:v2:teams": "teams:read",
        },
    )

    def get_claim_dict(self, request) -> dict[str, str]:
        """Return username (usually a uuid) instead of user pk in the 'sub' claim."""
        return {
            "sub": request.user.username,
            **self.get_additional_claims(request=request),
        }

    def get_additional_claims(self, request) -> dict[str, str | list[dict[str, str]]]:
        """
        Define the oidc user claims to support and how to get the data.

        https://django-oauth-toolkit.readthedocs.io/en/latest/oidc.html#adding-claims-to-the-id-token
        """
        claims = {}
        # is there a real user behind this request?
        if request.user.is_anonymous:
            return claims

        claims.update(
            {
                # standard OIDC claims
                "email": request.user.email,
                "email_verified": True,
                "updated_at": int(request.user.profile.updated.timestamp()),
                # bornhack custom claims
                "bornhack:v2:teams": [
                    {
                        "team": membership.team.name,
                        "camp": membership.team.camp.title,
                        "lead": membership.lead,
                    }
                    for membership in request.user.teammember_set.filter(approved=True)
                ],
                "bornhack:v2:permissions": list(request.user.get_all_permissions()),
                "bornhack:v2:groups": list(
                    request.user.groups.all().values_list("name", flat=True),
                ),
            },
        )

        # include bornhack:v2:public_credit_name?
        if (
            request.user.profile.public_credit_name_approved
            and request.user.profile.public_credit_name
        ):
            claims["bornhack:v2:public_credit_name"] = request.user.profile.public_credit_name

        # include location?
        if request.user.profile.location:
            claims["address"] = {"formatted": request.user.profile.location}

        # include phonenumber?
        if request.user.profile.phonenumber:
            claims["phone_number"] = request.user.profile.phonenumber
            claims["phone_number_verified"] = True

        # include profile description?
        if request.user.profile.description:
            claims["bornhack:v2:description"] = request.user.profile.description
        return claims

    def get_discovery_claims(self, request) -> list[str]:
        """Make oidc claims discoverable.

        https://django-oauth-toolkit.readthedocs.io/en/latest/oidc.html#supported-claims-discovery
        """
        return [
            # OIDC standard claims
            "address",
            "email",
            "email_verified",
            "nickname",
            "phone_number",
            "phone_number_verified",
            "sub",
            "updated_at",
            # custom user claims
            "bornhack:v2:description",
            "bornhack:v2:groups",
            "bornhack:v2:permissions",
            "bornhack:v2:public_credit_name",
            "bornhack:v2:teams",
        ]
