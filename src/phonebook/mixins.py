"""Phonebook Mixins."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet

from camps.mixins import CampViewMixin


class DectRegistrationViewMixin(CampViewMixin):
    """Mixin for limiting registrations to self.camp."""

    def get_object(self, *args, **kwargs) -> QuerySet:
        """Get the objects by camp."""
        return self.model.objects.get(camp=self.camp, number=self.kwargs["dect_number"])
