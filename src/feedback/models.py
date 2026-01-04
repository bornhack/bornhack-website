from __future__ import annotations

from django.db import models
from django.contrib.auth.models import User
from django_prometheus.models import ExportModelOperationsMixin
from django.utils import timezone

from utils.models import CampRelatedModel
from utils.models import UUIDModel


class Feedback(ExportModelOperationsMixin("feedback"), CampRelatedModel, UUIDModel):
    """Event feedback model"""

    class StateChoices(models.TextChoices):
        REVIEWED = "reviewed", "Reviewed"
        SPAM = "spam", "Spam"
        UNPROCESSED = "unprocessed", "Unprocessed"

    camp = models.ForeignKey(
        "camps.Camp",
        on_delete=models.PROTECT
    )

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT
    )

    feedback = models.TextField(
        help_text="Enter your feedback for this year's event"
    )

    state = models.CharField(
        choices = StateChoices.choices,
        default=StateChoices.UNPROCESSED,
        help_text="Set state of the feedback",
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    processed_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
    )

    def process_feedback(self, state: str, user: User) -> None:
        """
        Process feedback by changing the state, timestamp and user.

        When state arg is `StateChoices.UNPROCESSED`, the `processed_by`
        and `processed_at` fields get set to None.

        Raises a ValueError when state is invalid.
        """
        if not user.has_perm("camps.orga_team_member"):
            raise PermissionError(
                f"User: {user} is missing permissions for processing feedback"
            )

        # When state is invalid, this raises a ValueError.
        self.state = self.StateChoices(state.lower())

        if state == self.StateChoices.UNPROCESSED:
            self.processed_by = None
            self.processed_at = None
        else:
            self.processed_by = user
            self.processed_at = timezone.now()

        self.save()

