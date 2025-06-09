from __future__ import annotations

from django.db import models
from django.urls import reverse
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel
from utils.models import UUIDModel


class Ride(ExportModelOperationsMixin("ride"), UUIDModel, CampRelatedModel):
    camp = models.ForeignKey("camps.Camp", on_delete=models.PROTECT)
    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    author = models.CharField(
        max_length=100,
        help_text="Let people know who posted this",
        default="Anonymous",
    )
    has_car = models.BooleanField(
        default=True,
        help_text="Leave checked if you are offering a ride, uncheck if you need a ride.",
    )
    seats = models.PositiveIntegerField(
        help_text="How many seats are you offering/how many seats do you need?",
    )
    from_location = models.CharField(
        max_length=100,
        help_text="Where does this ride begin?",
    )
    to_location = models.CharField(
        max_length=100,
        help_text="What is the destination of this ride?",
    )
    when = models.DateTimeField(
        help_text="When does this ride leave? Format is YYYY-MM-DD HH:mm",
    )
    description = models.TextField(
        help_text="Include any details you want, like luggage space/requirements, contact info and so on.",
    )

    def get_absolute_url(self):
        return reverse(
            "rideshare:detail",
            kwargs={"pk": self.pk, "camp_slug": self.camp.slug},
        )

    def __str__(self) -> str:
        return f"{self.seats} seats from {self.from_location} to {self.to_location} at {self.when} by {self.user}"
