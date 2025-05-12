"""Model for phonebook."""

from __future__ import annotations

import logging
from typing import ClassVar

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel

from .dectutils import DectUtils

logger = logging.getLogger(f"bornhack.{__name__}")
dectutil = DectUtils()


class PhonebookDuplicateError(ValidationError):
    """Exception raised on duplicate number."""

    def __init__(self, number: str) -> None:
        """Exception raised on duplicate number."""
        super().__init__(f"The DECT number {number} is in use")


class PhonebookNumberError(ValidationError):
    """Exception raised on number error."""

    def __init__(self) -> None:
        """Exception raised on number error."""
        super().__init__("You must enter either a phonenumber or a letter representation of the phonenumber!")


class IPEIDuplicateError(ValidationError):
    """Exception raised on duplicate ipei."""

    def __init__(self, ipei: list[int]) -> None:
        """Exception raised on duplicate ipei."""
        super().__init__(f"The IPEI {dectutil.format_ipei(ipei[0], ipei[1])} is in use")


class PhonebookConflictLongError(ValidationError):
    """Exception raised on conflict with longer number."""

    def __init__(self, number: str) -> None:
        """Exception raised on conflict with longer number."""
        super().__init__(f"The DECT number {number} is not available, it conflicts with a longer number.")


class PhonebookConflictShortError(ValidationError):
    """Exception raised on conflict with shorter number."""

    def __init__(self, number: str) -> None:
        """Exception raised on conflict with shorter number."""
        super().__init__(f"The DECT number {number} is not available, it conflicts with a shorter number.")


class NumberNumericError(ValidationError):
    """Exception raised when number is not numeric."""

    def __init__(self) -> None:
        """Exception raised when number is not numeric."""
        super().__init__("Phonenumber must be numeric!")


class LettersNumberSizeError(ValidationError):
    """Exception raised on wrong number of letters or numbers."""

    def __init__(self, number: str, letters: str) -> None:
        """Exception raised on wrong number of letters or numbers."""
        super().__init__(f"Wrong number of letters ({len(letters)}) - should be {len(number)}")


class LetterNullOneError(ValidationError):
    """Exception raised on when 0 or 1 are used to express letters."""

    def __init__(self) -> None:
        """Exception raised on when 0 or 1 are used to express letters."""
        super().__init__("Numbers with 0 and 1 in them can not be expressed as letters")


class DigitError(ValidationError):
    """Exception raised on digit does not match the letter."""

    def __init__(self, digit: str, letter: str) -> None:
        """Exception raised on digit does not match the letter."""
        super().__init__(
            f"The digit '{digit}' does not match the letter '{letter}'. \
                         Valid letters for the digit '{digit}' are: {dectutil.DECT_MATRIX[digit]}"
        )


class DectRegistration(
    ExportModelOperationsMixin("dect_registration"),
    CampRelatedModel,
):
    """This model contains DECT registrations for users and services."""

    class Meta:
        """Meta."""

        unique_together: ClassVar[list[tuple[str]]] = [("camp", "number")]

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
        help_text="The letters or numbers chosen to represent this DECT number in the phonebook. "
                "Optional if you specify a number.",
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

    def save(self, *args, **kwargs) -> None:
        """This is just here so we get the validation in the admin as well."""
        # validate that the phonenumber and letters are valid and then save()
        self.clean_number()
        self.clean_letters()
        self.check_unique_ipei()
        super().save(*args, **kwargs)

    def check_unique_ipei(self) -> None:
        """Check IPEI is unique."""
        if (
            self.ipei
            and len(self.ipei) == 2  # noqa: PLR2004
            and DectRegistration.objects.filter(camp=self.camp, ipei=self.ipei).exclude(pk=self.pk).exists()
        ):
            raise IPEIDuplicateError(ipei=self.ipei)

    def clean_number(self) -> None:
        """We call this from the views form_valid() so we have a Camp object available for the validation.

        This code really belongs in model.clean(), but that gets called before form_valid()
        which is where we set the Camp object for the model instance.
        """
        # first check if we have a phonenumber...
        if not self.number:
            # we have no phonenumber, do we have some letters at least?
            if not self.letters:
                raise PhonebookNumberError
            # we have letters but not a number, let's deduce the numbers
            self.number = dectutil.letters_to_number(self.letters)

        # First of all, check that number is numeric
        try:
            int(self.number)
        except ValueError:
            raise NumberNumericError from None

        # check for conflicts with the same number
        if DectRegistration.objects.filter(camp=self.camp, number=self.number).exclude(pk=self.pk).exists():
            raise PhonebookDuplicateError(number=self.number)

        # check for conflicts with a longer number
        if (
            DectRegistration.objects.filter(
                camp=self.camp,
                number__startswith=self.number,
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise PhonebookConflictLongError

        # check if a shorter number is blocking
        i = len(self.number) - 1
        while i:
            if DectRegistration.objects.filter(camp=self.camp, number=self.number[:i]).exclude(pk=self.pk).exists():
                raise PhonebookConflictShortError
            i -= 1

    def clean_letters(self) -> None:
        """We call this from the views form_valid() so we have a Camp object available for the validation.

        This code really belongs in model.clean(), but that gets called before form_valid()
        which is where we set the Camp object for the model instance.
        """
        # if we have a letter representation of this number they should have the same length
        if self.letters:
            if len(self.letters) != len(self.number):
                raise LettersNumberSizeError

            # loop over the digits in the phonenumber
            combinations = list(dectutil.get_dect_letter_combinations(self.number))
            if not combinations:
                raise LetterNullOneError

            if self.letters.upper() not in list(combinations):
                # something is fucky, loop over letters to give a better error message
                for i, digit in enumerate(self.number):
                    if self.letters[i].upper() not in dectutil.DECT_MATRIX[digit]:
                        raise DigitError(digit=digit, letter=self.letters[i])
