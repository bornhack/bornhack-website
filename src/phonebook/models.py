import logging

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel

from .dectutils import DectUtils

logger = logging.getLogger("bornhack.%s" % __name__)
dectutil = DectUtils()


class DectRegistration(
    ExportModelOperationsMixin("dect_registration"),
    CampRelatedModel,
):
    """This model contains DECT registrations for users and services"""

    class Meta:
        unique_together = [("camp", "number")]

    camp = models.ForeignKey(
        "camps.Camp",
        related_name="dect_registrations",
        on_delete=models.PROTECT,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text="The django user who created this DECT registration",
    )

    number = models.CharField(
        max_length=9,
        blank=True,
        help_text="The DECT phonenumber, four digits or more. Optional if you specify letters.",
    )

    letters = models.CharField(
        max_length=9,
        blank=True,
        help_text="The letters or numbers chosen to represent this DECT number in the phonebook. Optional if you specify a number.",
    )

    description = models.TextField(
        blank=True,
        help_text="Description of this registration, like a name/handle, or a location or service name.",
    )

    activation_code = models.CharField(
        max_length=10,
        blank=True,
        help_text="The 10 digit numeric activation code",
    )

    publish_in_phonebook = models.BooleanField(
        default=True,
        help_text="Check to list this registration in the phonebook",
    )

    ipei = ArrayField(
        models.IntegerField(),
        blank=True,
        null=True,
        size=2,
        help_text="DECT phone IPEI (03562,0900847)",
    )

    def save(self, *args, **kwargs):
        """This is just here so we get the validation in the admin as well."""
        # validate that the phonenumber and letters are valid and then save()
        self.clean_number()
        self.clean_letters()
        self.check_unique_ipei()
        super().save(*args, **kwargs)

    def check_unique_ipei(self):
        if self.ipei and len(self.ipei) == 2:
            # check for conflicts with the same IPEI
            if DectRegistration.objects.filter(camp=self.camp, ipei=self.ipei).exclude(pk=self.pk).exists():
                raise ValidationError(
                    f"The IPEI {dectutil.format_ipei(self.ipei[0], self.ipei[1])} is in use",
                )

    def clean_number(self):
        """We call this from the views form_valid() so we have a Camp object available for the validation.
        This code really belongs in model.clean(), but that gets called before form_valid()
        which is where we set the Camp object for the model instance.
        """
        # first check if we have a phonenumber...
        if not self.number:
            # we have no phonenumber, do we have some letters at least?
            if not self.letters:
                raise ValidationError(
                    "You must enter either a phonenumber or a letter representation of the phonenumber!",
                )
            # we have letters but not a number, let's deduce the numbers
            self.number = dectutil.letters_to_number(self.letters)

        # First of all, check that number is numeric
        try:
            int(self.number)
        except ValueError:
            raise ValidationError("Phonenumber must be numeric!")

        # check for conflicts with the same number
        if DectRegistration.objects.filter(camp=self.camp, number=self.number).exclude(pk=self.pk).exists():
            raise ValidationError(f"The DECT number {self.number} is in use")

        # check for conflicts with a longer number
        if (
            DectRegistration.objects.filter(
                camp=self.camp,
                number__startswith=self.number,
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                f"The DECT number {self.number} is not available, it conflicts with a longer number.",
            )

        # check if a shorter number is blocking
        i = len(self.number) - 1
        while i:
            if DectRegistration.objects.filter(camp=self.camp, number=self.number[:i]).exclude(pk=self.pk).exists():
                raise ValidationError(
                    f"The DECT number {self.number} is not available, it conflicts with a shorter number.",
                )
            i -= 1

    def clean_letters(self):
        """We call this from the views form_valid() so we have a Camp object available for the validation.
        This code really belongs in model.clean(), but that gets called before form_valid()
        which is where we set the Camp object for the model instance.
        """
        # if we have a letter representation of this number they should have the same length
        if self.letters:
            if len(self.letters) != len(self.number):
                raise ValidationError(
                    f"Wrong number of letters ({len(self.letters)}) - should be {len(self.number)}",
                )

            # loop over the digits in the phonenumber
            combinations = list(dectutil.get_dect_letter_combinations(self.number))
            if not combinations:
                raise ValidationError(
                    "Numbers with 0 and 1 in them can not be expressed as letters",
                )

            if self.letters.upper() not in list(combinations):
                # something is fucky, loop over letters to give a better error message
                i = 0
                for digit in self.number:
                    if self.letters[i].upper() not in dectutil.DECT_MATRIX[digit]:
                        raise ValidationError(
                            f"The digit '{digit}' does not match the letter '{self.letters[i]}'. Valid letters for the digit '{digit}' are: {dectutil.DECT_MATRIX[digit]}",
                        )
                    i += 1
