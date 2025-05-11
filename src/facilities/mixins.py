from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from camps.mixins import CampViewMixin

from .models import Facility
from .models import FacilityType


class FacilityTypeViewMixin(CampViewMixin):
    """A mixin to get the FacilityType object based on facility_type_slug in url kwargs"""

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.facility_type = get_object_or_404(
            FacilityType,
            responsible_team__camp=self.camp,
            slug=self.kwargs["facility_type_slug"],
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["facilitytype"] = self.facility_type
        return context


class FacilityViewMixin(CampViewMixin):
    """Mixin shared between views dealing with a facility."""

    def setup(self, *args, **kwargs):
        """Get facility from kwargs."""
        super().setup(*args, **kwargs)
        self.facility = get_object_or_404(Facility, uuid=kwargs["facility_uuid"])

    def get_form(self, *args, **kwargs):
        """The default range widgets are a bit shit because they eat the help_text and
        have no indication of which field is for what. So we add a nice placeholder.
        """
        form = super().get_form(*args, **kwargs)
        if "when" in form.fields:
            form.fields["when"].widget.widgets[0].attrs = {
                "placeholder": f"Open Date and Time (YYYY-MM-DD HH:MM). Active time zone is {settings.TIME_ZONE}.",
            }
            form.fields["when"].widget.widgets[1].attrs = {
                "placeholder": f"Close Date and Time (YYYY-MM-DD HH:MM). Active time zone is {settings.TIME_ZONE}.",
            }
        return form

    def get_context_data(self, **kwargs):
        """Add facility to context."""
        context = super().get_context_data(**kwargs)
        context["facility"] = self.facility
        return context


class FacilityFacilitatorViewMixin(FacilityViewMixin):
    """Mixins for views only available to users with facilitator permission for the team responsible for the facility type or gis team members."""

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if self.request.user.has_perm("camps.gis_team_member"):
            return
        if (
            self.facility.facility_type.responsible_team.facilitator_permission_set
            not in request.user.get_all_permissions()
        ):
            messages.error(request, "No thanks")
            raise PermissionDenied()
