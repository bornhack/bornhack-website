from django.shortcuts import get_object_or_404

from camps.mixins import CampViewMixin

from .models import Facility, FacilityType


class FacilityTypeViewMixin(CampViewMixin):
    """
    A mixin to get the FacilityType object based on facility_type_slug in url kwargs
    """

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


class FacilityViewMixin(FacilityTypeViewMixin):
    """
    A mixin to get the Facility object based on facility_uuid in url kwargs
    """

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.facility = get_object_or_404(
            Facility,
            facility_type=self.facility_type,
            uuid=self.kwargs["facility_uuid"],
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["facility"] = self.facility
        return context
