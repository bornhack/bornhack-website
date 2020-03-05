import logging

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from utils.models import CampRelatedModel

from .dectutils import DectUtils

logger = logging.getLogger("bornhack.%s" % __name__)


class DectRegistration(CampRelatedModel):
    """
    This model contains DECT registrations for users and services
    """

    class Meta:
        unique_together = [("camp", "number")]

    camp = models.ForeignKey(
        "camps.Camp", related_name="dect_registrations", on_delete=models.PROTECT,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text="The django user who created this DECT registration",
    )

    number = models.CharField(
        max_length=9, help_text="The DECT number, numeric or as letters",
    )

    letters = models.CharField(
        max_length=9,
        blank=True,
        help_text="The letters chosen to represent this DECT number in the phonebook. Optional.",
    )

    description = models.TextField(
        blank=True,
        help_text="Description of this registration, like a name or a location or a service.",
    )

    activation_code = models.CharField(
        max_length=10, blank=True, help_text="The 10 digit numeric activation code",
    )

    publish_in_phonebook = models.BooleanField(
        default=True, help_text="Check to list this registration in the phonebook",
    )

    def save(self, *args, **kwargs):
        """
        This is just here so we get the validation in the admin as well.
        """
        self.clean_number()
        self.clean_letters()
        super().save(*args, **kwargs)

    def clean_number(self):
        """
        We call this from the views form_valid() so we have a Camp object available for the validation.
        This code really belongs in model.clean(), but that gets called before form_valid()
        which is where we set the Camp object for the model instance.
        """
        # check for conflicts with the same number
        if (
            DectRegistration.objects.filter(camp=self.camp, number=self.number)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError("This DECT number is in use")

        # check for conflicts with a longer number
        if (
            DectRegistration.objects.filter(
                camp=self.camp, number__startswith=self.number
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                "This DECT number is not available, it conflicts with a longer number."
            )

        # check if a shorter number is blocking
        i = len(self.number) - 1
        while i:
            if (
                DectRegistration.objects.filter(camp=self.camp, number=self.number[:i])
                .exclude(pk=self.pk)
                .exists()
            ):
                raise ValidationError(
                    "This DECT number is not available, it conflicts with a shorter number."
                )
            i -= 1

    def clean_letters(self):
        """
        We call this from the views form_valid() so we have a Camp object available for the validation.
        This code really belongs in model.clean(), but that gets called before form_valid()
        which is where we set the Camp object for the model instance.
        """
        # if we have a letter representation of this number they should have the same length
        if self.letters:
            if len(self.letters) != len(self.number):
                raise ValidationError(
                    f"Wrong number of letters ({len(self.letters)}) - should be {len(self.number)}"
                )

            # loop over the digits in the phonenumber
            dectutil = DectUtils()
            combinations = list(dectutil.get_dect_letter_combinations(self.number))
            if not combinations:
                raise ValidationError(
                    "Numbers with 0 and 1 in them can not be expressed as letters"
                )

            if self.letters not in list(combinations):
                # something is fucky, loop over letters to give a better error message
                i = 0
                for digit in self.number:
                    if self.letters[i].upper() not in dectutil.DECT_MATRIX[digit]:
                        raise ValidationError(
                            f"The digit '{digit}' does not match the letter '{self.letters[i]}'. Valid letters for the digit '{digit}' are: {dectutil.DECT_MATRIX[digit]}"
                        )
                    i += 1
