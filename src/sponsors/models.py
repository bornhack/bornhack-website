from __future__ import annotations

from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel


def get_sponsor_upload_path(instance, filename):
    return "public/sponsors/{camp_slug}/{filename}".format(
        camp_slug=instance.tier.camp.slug,
        filename="{}_logo.{}".format(instance.name.lower(), filename.split(".")[-1]),
    )


class Sponsor(ExportModelOperationsMixin("sponsor"), CampRelatedModel):
    name = models.CharField(max_length=150, help_text="Name of the sponsor")

    tier = models.ForeignKey("sponsors.SponsorTier", on_delete=models.PROTECT)

    description = models.TextField(help_text="A short description of the sponsorship")

    logo_filename = models.CharField(max_length=255, help_text="Filename of the logo")

    url = models.URLField(null=True, blank=True, help_text="An URL to the sponsor.")

    week_tickets = models.IntegerField(
        null=True,
        blank=True,
        help_text="The number of full week tickets to generate for this sponsor.",
    )

    oneday_tickets = models.IntegerField(
        null=True,
        blank=True,
        help_text="The number of one day tickets to generate for this sponsor.",
    )

    tickets_generated = models.BooleanField(default=False)

    ticket_email = models.EmailField(
        null=True,
        blank=True,
        help_text="The email to send the tickets to",
    )

    ticket_ready = models.BooleanField(
        default=False,
        help_text="Check when we are ready to generate and send tickets to this sponsor.",
    )

    tickets_sent = models.BooleanField(
        default=False,
        help_text="True when the tickets have been emailed to the sponsor",
    )

    def __str__(self):
        return f"{self.name} ({self.tier.camp})"

    @property
    def camp(self):
        return self.tier.camp

    camp_filter = "tier__camp"


class SponsorTier(ExportModelOperationsMixin("sponsor_tier"), CampRelatedModel):
    name = models.CharField(
        max_length=25,
        help_text="Name of the tier (gold, silver, etc.)",
    )

    description = models.TextField(help_text="A description of what the tier includes.")

    camp = models.ForeignKey(
        "camps.Camp",
        null=True,
        on_delete=models.PROTECT,
        related_name="sponsor_tiers",
        help_text="The camp this sponsor tier belongs to",
    )

    weight = models.IntegerField(
        default=0,
        help_text="""This decides where on the list the tier will be shown. I.e.
        gold should have a lower value than silver.""",
    )

    week_tickets = models.IntegerField(
        help_text="The default number of full week tickets generated for a sponsor in this tier.",
    )

    oneday_tickets = models.IntegerField(
        default=0,
        help_text="The default number of one day tickets generated for a sponsor in this tier.",
    )

    def __str__(self):
        return f"{self.name} ({self.camp})"
