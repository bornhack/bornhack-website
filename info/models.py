from __future__ import unicode_literals
from django.contrib import messages
from django.db import models
from utils.models import CreatedUpdatedModel
from django.core.exceptions import ValidationError


class InfoCategory(CreatedUpdatedModel):
    class Meta:
        ordering = ['-weight', 'headline']
        unique_together = (('anchor', 'camp'), ('headline', 'camp'))

    camp = models.ForeignKey(
        'camps.Camp',
        related_name = 'infocategories',
        on_delete = models.PROTECT
    )

    headline = models.CharField(
        max_length = 100,
        help_text = "The headline of this info category"
    )

    anchor = models.SlugField(
        help_text = "The HTML anchor to use for this info category."
    )

    weight = models.PositiveIntegerField(
        help_text = 'Determines sorting/ordering. Heavier categories sink to the bottom. Categories with the same weight are ordered alphabetically.'
    )

    def clean(self):
        if InfoItem.objects.filter(camp=self.camp, anchor=self.anchor).exists():
            # this anchor is already in use on an item, so it cannot be used (must be unique on the page)
            raise ValidationError({'anchor': 'Anchor is already in use on an info item for this camp'})


class InfoItem(CreatedUpdatedModel):
    class Meta:
        ordering = ['-weight', 'headline']
        unique_together = (('anchor', 'category'), ('headline', 'category'))

    category = models.ForeignKey(
        'info.InfoCategory',
        related_name = 'infoitems',
        on_delete = models.PROTECT
    )

    headline = models.CharField(
        max_length = 100,
        help_text = "Headline of this info item."
    )

    anchor = models.SlugField(
        help_text = "The HTML anchor to use for this info item."
    )

    body = models.TextField(
        help_text = 'Body of this info item. Markdown is supported.'
    )

    weight = models.PositiveIntegerField(
        help_text = 'Determines sorting/ordering. Heavier items sink to the bottom. Items with the same weight are ordered alphabetically.'
    )

    def clean(self):
        if InfoCategory.objects.filter(camp=self.camp, anchor=self.anchor).exists():
            # this anchor is already in use on a category, so it cannot be used here (they must be unique on the entire page)
            raise ValidationError({'anchor': 'Anchor is already in use on an info category for this camp'})


