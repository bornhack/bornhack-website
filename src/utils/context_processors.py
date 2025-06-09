from __future__ import annotations


def is_volunteer(request):
    """Check if user has 'camps.<team>_team_member' permission for any team."""
    for perm in request.user.get_all_permissions():
        if perm.endswith("_team_member"):
            # user is a member of some team
            return {"is_volunteer": True}
    return {"is_volunteer": False}
