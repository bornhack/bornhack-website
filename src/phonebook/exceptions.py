"""Exceptions for phonebook."""

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError

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
                         Valid letters for the digit '{digit}' are: {dectutil.DECT_MATRIX[digit]}",
        )


class InvalidIPEIError(ValidationError):
    """Exception raised on invalid IPEI."""

    def __init__(self, ipei: list[int]) -> None:
        """Exception raised when an invalid is used."""
        super().__init__(f"unable to process IPEI {ipei}.")
