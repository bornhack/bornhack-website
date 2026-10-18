"""Custom managers and querysets for the Program app."""

from __future__ import annotations

from typing import Self

from django.db import models
from django.db.models import Q


class EventTypeQuerySet(models.QuerySet):
    """Custom qs for the Camp model."""

    def annotate_event_count(self, camp: Camp) -> Self:
        """Annotate the number of events of each type for the camp."""
        return self.annotate(
            event_count=models.Count("events", filter=Q(events__track__camp__uuid=camp.uuid)),
        )
