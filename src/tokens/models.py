"""All models for the token application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel

if TYPE_CHECKING:
    from typing import ClassVar

    from camps.models import Camp


class Token(ExportModelOperationsMixin("token"), CampRelatedModel):
    """Token model."""

    class Meta:
        """Meta class definition for Token model"""

        unique_together = ("camp", "token")
        ordering: ClassVar[list[str]] = ["camp"]

    camp = models.ForeignKey("camps.Camp", on_delete=models.PROTECT)

    token = models.CharField(max_length=32, help_text="The secret token")

    category = models.TextField(
        help_text="The category/hint for this token (physical, website, whatever)",
    )

    description = models.TextField(help_text="The description of the token")

    active = models.BooleanField(
        default=False,
        help_text="An active token is listed and can be found by players, "
        "an inactive token is unlisted and returns an error saying 'valid "
        "but inactive token found' to players who find it.",
    )

    valid_when = DateTimeRangeField(
        db_index=True,
        null=True,
        blank=True,
        help_text="Token valid start/end time. YYYY-MM-DD HH:MM:SS. Optional.",
    )

    camp_filter = "camp"

    def __str__(self) -> str:
        """String formatter."""
        return f"{self.description} ({self.camp})"

    def get_absolute_url(self) -> str:
        """Get absolute url."""
        return reverse(
            "backoffice:token_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.pk},
        )

    @property
    def valid_now(self) -> bool:
        """Returns if the token is valid 'now'."""
        valid = False
        if not self.valid_when:
            # no time limit
            valid = True
        elif self.valid_when.lower and self.valid_when.lower > timezone.now():
            # not valid yet
            valid = False
        elif self.valid_when.upper and self.valid_when.upper < timezone.now():
            # not valid anymore
            valid = False
        elif self.valid_when.lower and self.valid_when.lower < timezone.now():
            # is valid
            valid = True
        return valid


class TokenFind(ExportModelOperationsMixin("token_find"), CampRelatedModel):
    """Model for submitting the found token."""

    class Meta:
        """Meta."""

        unique_together = ("user", "token")

    token = models.ForeignKey("tokens.Token", on_delete=models.PROTECT)

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="token_finds",
    )

    camp_filter = "token__camp"

    def __str__(self) -> str:
        """String formatter."""
        return f"{self.token} found by {self.user}"

    @property
    def camp(self) -> Camp:
        """Property camp linked to this token find via Token."""
        return self.token.camp
