"""The Wish model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.urls import reverse
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel
from utils.slugs import unique_slugify

if TYPE_CHECKING:
    from camps.models import Camp


class Wish(ExportModelOperationsMixin("wish"), CampRelatedModel):
    """This model contains the stuff BornHack needs.

    This can be anything from kitchen equipment to network cables, or anything really.
    """

    class Meta:
        """Model configuration."""

        verbose_name_plural = "wishes"

    name = models.CharField(
        max_length=100,
        help_text="Short description of the wish",
    )

    slug = models.SlugField(
        blank=True,
        unique=True,
        help_text="The url slug for this wish. Leave blank to autogenerate one.",
    )

    description = models.TextField(
        help_text="Description of the needed item. Markdown is supported!",
    )

    count = models.IntegerField(
        default=1,
        help_text="How many do we need?",
    )

    fulfilled = models.BooleanField(
        default=False,
        help_text="A Wish is marked as fulfilled when we no longer need the thing.",
    )

    team = models.ForeignKey(
        "teams.Team",
        help_text="The team that needs this thing. When in doubt pick Orga :)",
        on_delete=models.PROTECT,
        related_name="wishes",
    )

    @property
    def camp(self) -> Camp:
        """Return the camp object."""
        return self.team.camp

    camp_filter = "team__camp"

    def __str__(self) -> str:
        """Return the name."""
        return self.name

    def save(self, **kwargs: dict[str, str]) -> None:
        """Set slug and save."""
        self.slug = unique_slugify(
            self.name,
            slugs_in_use=self.__class__.objects.filter(team=self.team).values_list(
                "slug",
                flat=True,
            ),
        )
        super().save(**kwargs)

    def get_absolute_url(self) -> str:
        """Return URL to detailview."""
        return reverse(
            "wishlist:detail",
            kwargs={
                "camp_slug": self.camp.slug,
                "wish_slug": self.slug,
            },
        )
