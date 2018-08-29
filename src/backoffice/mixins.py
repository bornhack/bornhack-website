from utils.mixins import RaisePermissionRequiredMixin


class OrgaTeamPermissionMixin(RaisePermissionRequiredMixin):
    """
    Permission mixin for views used by Orga Team
    """
    permission_required = ("camps.backoffice_permission", "camps.orgateam_permission")


class EconomyTeamPermissionMixin(RaisePermissionRequiredMixin):
    """
    Permission mixin for views used by Economy Team
    """
    permission_required = ("camps.backoffice_permission", "camps.economyteam_permission")


class InfoTeamPermissionMixin(RaisePermissionRequiredMixin):
    """
    Permission mixin for views used by Info Team/InfoDesk
    """
    permission_required = ("camps.backoffice_permission", "camps.infoteam_permission")


class ContentTeamPermissionMixin(RaisePermissionRequiredMixin):
    """
    Permission mixin for views used by Content Team
    """
    permission_required = ("camps.backoffice_permission", "program.contentteam_permission")

