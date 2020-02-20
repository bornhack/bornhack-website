import logging

from django.contrib.gis.db.models import PointField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from utils.models import CampRelatedModel, UUIDModel

logger = logging.getLogger("bornhack.%s" % __name__)


class FacilityQuickFeedback(models.Model):
    """
    This model contains the various options for giving quick feedback which we present to the user
    when giving feedback on facilities. Think "Needs cleaning" or "Doesn't work" and such.
    This model is not Camp specific.
    """

    feedback = models.CharField(max_length=100)

    icon = models.CharField(
        max_length=100,
        default="fas fa-exclamation",
        blank=True,
        help_text="Name of the fontawesome icon to use, including the 'fab fa-' or 'fas fa-' part. Defaults to an exclamation mark icon.",
    )

    def __str__(self):
        return self.feedback


class FacilityType(CampRelatedModel):
    """
    Facility types are used to group similar facilities, like Toilets, Showers, Thrashcans...
    facilities.Type has a m2m relationship with FeedbackChoice which determines which choices
    are presented for giving feedback for this Facility
    """

    class Meta:
        unique_together = [("slug", "responsible_team")]

    name = models.CharField(max_length=100, help_text="The name of this facility type")

    slug = models.SlugField(
        blank=True,
        help_text="The url slug for this facility type. Leave blank to autogenerate one.",
    )

    description = models.TextField(help_text="Description of this facility type")

    icon = models.CharField(
        max_length=100,
        default="fas fa-list",
        blank=True,
        help_text="Name of the fontawesome icon to use, including the 'fab fa-' or 'fas fa-' part.",
    )

    responsible_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        help_text="The Team responsible for this type of facility. This team will get the notification when we get a new FacilityFeedback for a Facility of this type.",
    )

    quickfeedback_options = models.ManyToManyField(
        to="facilities.FacilityQuickFeedback",
        help_text="Pick the quick feedback options the user should be presented with when submitting Feedback for a Facility of this type. Pick at least the 'N/A' option if none of the other applies.",
    )

    @property
    def camp(self):
        return self.responsible_team.camp

    camp_filter = "responsible_team__camp"

    def __str__(self):
        return f"{self.name} ({self.camp})"

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.slug:
            raise ValidationError("Unable to slugify")
        super().save(**kwargs)


class Facility(CampRelatedModel, UUIDModel):
    """
    Facilities are toilets, thrashcans, cooking and dishwashing areas, and any other part of the event which could need attention or maintenance.
    """

    facility_type = models.ForeignKey(
        "facilities.FacilityType", related_name="facilities", on_delete=models.PROTECT
    )

    name = models.CharField(
        max_length=100, help_text="Name or description of this facility",
    )

    description = models.TextField(help_text="Description of this facility")

    location = PointField(help_text="The location of this facility")

    @property
    def team(self):
        return self.facility_type.responsible_team

    @property
    def camp(self):
        return self.facility_type.camp

    camp_filter = "facility_type__responsible_team__camp"

    def __str__(self):
        return self.name


class FacilityFeedback(CampRelatedModel):
    """
    This model contains participant feedback for Facilities.
    It is linked to the user and the facility, and to the
    quick_feedback choice the user picked (if any).
    """

    user = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="facility_feebacks",
        help_text="The User this feedback came from, empty if the user submits anonymously",
    )

    facility = models.ForeignKey(
        "facilities.Facility",
        related_name="feedbacks",
        on_delete=models.PROTECT,
        help_text="The Facility this feeback is about",
    )

    quick_feedback = models.ForeignKey(
        "facilities.FacilityQuickFeedback",
        on_delete=models.PROTECT,
        related_name="feedbacks",
        help_text="Quick feedback options. Elaborate in comment field as needed.",
    )

    comment = models.TextField(
        blank=True, help_text="Any comments or feedback about this facility? (optional)"
    )

    urgent = models.BooleanField(
        default=False,
        help_text="Check if this is an urgent issue. Will trigger immediate notifications to the responsible team.",
    )

    handled = models.BooleanField(
        default=False,
        help_text="True if this feedback has been handled by the responsible team, False if not",
    )

    handled_by = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="facility_feebacks_handled",
        help_text="The User who handled this feedback",
    )

    @property
    def camp(self):
        return self.facility.camp

    camp_filter = "facility__facility_type__responsible_team__camp"
