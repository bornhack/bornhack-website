from camps.mixins import CampViewMixin
from utils.mixins import StaffMemberRequiredMixin


class BackofficeViewMixin(CampViewMixin, StaffMemberRequiredMixin):
    """
    Mixin used by all backoffice views. For now just uses CampViewMixin and StaffMemberRequiredMixin.
    """
    pass

