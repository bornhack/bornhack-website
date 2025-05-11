import base64
import io
import logging

import qrcode
from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import Point
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib.postgres.fields import RangeOperators
from django.db import models
from django.shortcuts import reverse
from django_prometheus.models import ExportModelOperationsMixin

from maps.utils import LeafletMarkerChoices
from utils.models import CampRelatedModel
from utils.models import UUIDModel
from utils.slugs import unique_slugify

logger = logging.getLogger("bornhack.%s" % __name__)


class FacilityQuickFeedback(
    ExportModelOperationsMixin("facility_quick_feedback"),
    models.Model,
):
    """This model contains the various options for giving quick feedback which we present to the user
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


class FacilityType(ExportModelOperationsMixin("facility_type"), CampRelatedModel):
    """Facility types are used to group similar facilities, like Toilets, Showers, Thrashcans...
    facilities.Type has a m2m relationship with FeedbackChoice which determines which choices
    are presented for giving feedback for facilities of this type
    """

    class Meta:
        # we need a unique slug for each team due to the url structure in backoffice
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

    marker = models.CharField(
        max_length=10,
        choices=LeafletMarkerChoices.choices,
        default=LeafletMarkerChoices.BLUE,
        help_text="The name/colour of the Leaflet marker to use for this facility type.",
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
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.filter(
                    responsible_team=self.responsible_team,
                ).values_list("slug", flat=True),
            )
        super().save(**kwargs)


class Facility(ExportModelOperationsMixin("facility"), CampRelatedModel, UUIDModel):
    """Facilities are toilets, thrashcans, cooking and dishwashing areas, and any other part of the event which could need attention or maintenance."""

    facility_type = models.ForeignKey(
        "facilities.FacilityType",
        related_name="facilities",
        on_delete=models.PROTECT,
    )

    name = models.CharField(
        max_length=100,
        help_text="Name or description of this facility",
    )

    description = models.TextField(help_text="Description of this facility")

    # default to near the workshop rooms / cabins
    location = PointField(
        default=Point(9.93891, 55.38562),
        help_text="The location of this facility.",
    )

    @property
    def team(self):
        return self.facility_type.responsible_team

    @property
    def camp(self):
        return self.facility_type.camp

    camp_filter = "facility_type__responsible_team__camp"

    def __str__(self):
        return self.name

    def get_feedback_url(self, request):
        return request.build_absolute_uri(
            reverse(
                "facilities:facility_feedback",
                kwargs={
                    "camp_slug": self.facility_type.responsible_team.camp.slug,
                    "facility_type_slug": self.facility_type.slug,
                    "facility_uuid": self.uuid,
                },
            ),
        )

    def get_feedback_qr(self, request):
        qr = qrcode.make(
            self.get_feedback_url(request),
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
        ).resize((250, 250))
        file_like = io.BytesIO()
        qr.save(file_like, format="png")
        qrcode_base64 = base64.b64encode(file_like.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{qrcode_base64}"

    def unhandled_feedbacks(self):
        return self.feedbacks.filter(handled=False)


class FacilityFeedback(
    ExportModelOperationsMixin("facility_feedback"),
    CampRelatedModel,
):
    """This model contains participant feedback for Facilities.
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
        blank=True,
        help_text="Any comments or feedback about this facility? (optional)",
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


class FacilityOpeningHours(
    ExportModelOperationsMixin("facility_opening_hours"),
    CampRelatedModel,
):
    """This model contains opening hours for facilities which are not always open.
    If a facility has zero entries in this model it means is always open.
    If a facility has one or more periods of opening hours defined in this model
    it is considered closed outside of the period(s) defined in this model.
    """

    class Meta:
        ordering = ["when"]
        constraints = [
            # we do not want overlapping hours for the same Facility
            ExclusionConstraint(
                name="prevent_facility_opening_hours_overlaps",
                expressions=[
                    ("when", RangeOperators.OVERLAPS),
                    ("facility", RangeOperators.EQUAL),
                ],
            ),
        ]

    facility = models.ForeignKey(
        "facilities.Facility",
        related_name="opening_hours",
        on_delete=models.PROTECT,
        help_text="The Facility to which these opening hours belong.",
    )

    when = DateTimeRangeField(
        db_index=True,
        help_text="The period when this facility is open.",
    )

    notes = models.TextField(
        blank=True,
        help_text="Any notes for this period like 'no hot food after 20' or 'no alcohol sale after 02'. Optional.",
    )

    @property
    def camp(self):
        return self.facility.camp

    camp_filter = "facility__facility_type__responsible_team__camp"

    @property
    def duration(self):
        return self.when.upper - self.when.lower
