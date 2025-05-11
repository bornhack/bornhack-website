from __future__ import annotations

from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel


class Token(ExportModelOperationsMixin("token"), CampRelatedModel):
    camp = models.ForeignKey("camps.Camp", on_delete=models.PROTECT)

    token = models.CharField(max_length=32, help_text="The secret token")

    category = models.TextField(
        help_text="The category/hint for this token (physical, website, whatever)",
    )

    description = models.TextField(help_text="The description of the token")

    active = models.BooleanField(
        default=False,
        help_text="An active token is listed and can be found by players, an inactive token is unlisted and returns an error saying 'valid but inactive token found' to players who find it.",
    )

    valid_when = DateTimeRangeField(
        db_index=True,
        null=True,
        blank=True,
        help_text="Token valid start/end time. YYYY-MM-DD HH:MM:SS. Optional.",
    )

    camp_filter = "camp"

    def __str__(self):
        return f"{self.description} ({self.camp})"

    class Meta:
        ordering = ["camp"]

    def get_absolute_url(self):
        return reverse(
            "backoffice:token_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.pk},
        )

    @property
    def valid_now(self):
        if not self.valid_when:
            # no time limit
            return True
        if self.valid_when.lower and self.valid_when.lower > timezone.now():
            # not valid yet
            return False
        if self.valid_when.upper and self.valid_when.upper < timezone.now():
            # not valid anymore
            return False
        return True


class TokenFind(ExportModelOperationsMixin("token_find"), CampRelatedModel):
    class Meta:
        unique_together = ("user", "token")

    token = models.ForeignKey("tokens.Token", on_delete=models.PROTECT)

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="token_finds",
    )

    camp_filter = "token__camp"

    def __str__(self):
        return f"{self.token} found by {self.user}"

    @property
    def camp(self):
        return self.token.camp
