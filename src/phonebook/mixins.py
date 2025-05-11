from __future__ import annotations

from camps.mixins import CampViewMixin

# from .models import DectRegistration


class DectRegistrationViewMixin(CampViewMixin):
    def get_object(self, *args, **kwargs):
        return self.model.objects.get(camp=self.camp, number=self.kwargs["dect_number"])
