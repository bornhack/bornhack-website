from __future__ import annotations

import reversion
from django.core.exceptions import ValidationError
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel


class InfoCategory(ExportModelOperationsMixin("info_category"), CampRelatedModel):
    class Meta:
        ordering = ["weight", "headline"]
        verbose_name_plural = "Info Categories"

    headline = models.CharField(
        max_length=100,
        help_text="The headline of this info category",
    )

    anchor = models.SlugField(
        help_text="The HTML anchor to use for this info category.",
    )

    weight = models.PositiveIntegerField(
        help_text="Determines sorting/ordering. Heavier categories sink to the bottom. Categories with the same weight are ordered alphabetically. Defaults to 100.",
        default=100,
    )

    team = models.ForeignKey(
        "teams.Team",
        help_text="The team responsible for this info category.",
        on_delete=models.PROTECT,
        related_name="info_categories",
    )

    def clean(self):
        if InfoItem.objects.filter(
            category__team__camp=self.camp,
            anchor=self.anchor,
        ).exists():
            # this anchor is already in use on an item, so it cannot be used (must be unique on the page)
            raise ValidationError(
                {"anchor": "Anchor is already in use on an info item for this camp"},
            )

    @property
    def camp(self):
        return self.team.camp

    camp_filter = "team__camp"

    def __str__(self):
        return f"{self.headline} ({self.camp})"


# We want to have info items under version control
@reversion.register()
class InfoItem(ExportModelOperationsMixin("info_item"), CampRelatedModel):
    class Meta:
        ordering = ["weight", "headline"]
        unique_together = (("anchor", "category"), ("headline", "category"))

    category = models.ForeignKey(
        "info.InfoCategory",
        related_name="infoitems",
        on_delete=models.PROTECT,
    )

    headline = models.CharField(max_length=100, help_text="Headline of this info item.")

    anchor = models.SlugField(help_text="The HTML anchor to use for this info item.")

    body = models.TextField(help_text="Body of this info item. Markdown is supported.")

    weight = models.PositiveIntegerField(
        help_text="Determines sorting/ordering. Heavier items sink to the bottom. Items with the same weight are ordered alphabetically. Defaults to 100.",
        default=100,
    )

    @property
    def camp(self):
        return self.category.camp

    camp_filter = "category__team__camp"

    def clean(self):
        if (
            hasattr(self, "category")
            and InfoCategory.objects.filter(
                team__camp=self.category.team.camp,
                anchor=self.anchor,
            ).exists()
        ):
            # this anchor is already in use on a category, so it cannot be used here (they must be unique on the entire page)
            raise ValidationError(
                {
                    "anchor": "Anchor is already in use on an info category for this camp",
                },
            )

    def __str__(self):
        return f"{self.headline} ({self.category})"
