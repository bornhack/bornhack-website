from django.db import models

from utils.models import CampRelatedModel


def get_sponsor_upload_path(instance, filename):
    return 'public/sponsors/{camp_slug}/{filename}'.format(
        camp_slug=instance.tier.camp.slug,
        filename='{}_logo.{}'.format(
            instance.name.lower(),
            filename.split('.')[-1]
        )
    )


class Sponsor(CampRelatedModel):
    name = models.CharField(
        max_length=150,
        help_text='Name of the sponsor'
    )

    tier = models.ForeignKey('sponsors.SponsorTier', on_delete=models.PROTECT)

    description = models.TextField(
        help_text='A short description of the sponsorship'
    )

    logo = models.URLField(
        max_length=255,
        help_text='A URL to the logo'
    )

    url = models.URLField(
        null=True,
        blank=True,
        help_text="An URL to the sponsor."
    )

    def __str__(self):
        return '{} ({})'.format(self.name, self.tier.camp)

    @property
    def camp(self):
        return self.tier.camp


class SponsorTier(CampRelatedModel):
    name = models.CharField(
        max_length=25,
        help_text='Name of the tier (gold, silver, etc.)'
    )

    description = models.TextField(
        help_text='A description of what the tier includes.'
    )

    camp = models.ForeignKey(
        'camps.Camp',
        null=True,
        on_delete=models.PROTECT,
        related_name='sponsor_tiers',
        help_text='The camp this sponsor tier belongs to',
    )

    weight = models.IntegerField(
        default=0,
        help_text="""This decides where on the list the tier will be shown. I.e.
        gold should have a lower value than silver."""
    )

    def __str__(self):
        return '{} ({})'.format(self.name, self.camp)
