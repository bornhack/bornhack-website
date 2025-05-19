"""Exceptions for phonebook."""

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError

logger = logging.getLogger(f"bornhack.{__name__}")


class ReservedIrcNameError(ValidationError):
    """Exception raised on reserved irc name."""

    def __init__(self) -> None:
        """Exception raised on reserved irc name."""
        super().__init__("The public IRC channel name is reserved")


class IrcChannelInUseError(ValidationError):
    """Exception raised a public irc channel is in use."""

    def __init__(self) -> None:
        """Exception raised a public irc channel is in use."""
        super().__init__("The public IRC channel name is already in use on another team!")

class StartAfterEndError(ValidationError):
    """Exception raised when start date is after end date."""

    def __init__(self) -> None:
        """Exception raised when start date is after end date."""
        super().__init__("Start can not be after end.")

class StartSameAsEndError(ValidationError):
    """Exception raised when start date is the same as end date."""

    def __init__(self) -> None:
        """Exception raised when start date is the same as end date."""
        super().__init__("Start can not be the same as end.")
