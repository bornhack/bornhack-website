from oauth2_provider.oauth2_validators import OAuth2Validator


class BornhackOAuth2Validator(OAuth2Validator):
    oidc_claim_scope = {}
    oidc_claim_scope.update({"sub": "openid"})  # Needed to make the page happy
    oidc_claim_scope.update({"profile": "profile:read"})
    oidc_claim_scope.update({"user": "profile:read"})
    oidc_claim_scope.update({"teams": "profile:read"})

    def get_additional_claims(self, request):
        return {
            "profile": {
                "public_credit_name": request.user.profile.get_public_credit_name,
                "description": request.user.profile.description,
            },
            "user": {
                "username": request.user.username,
                "user_id": request.user.id,
            },
            "teams": [
                {"team": team.name, "camp": team.camp.title}
                for team in request.user.teams.all()
            ],
        }
