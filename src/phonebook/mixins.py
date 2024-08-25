from typing import Any

from camps.mixins import CampViewMixin


class DectRegistrationViewMixin(CampViewMixin):
    def get_object(self, *args: list[Any], **kwargs: dict[str, Any]):
        return self.model.objects.get(camp=self.camp, number=self.kwargs["dect_number"])
