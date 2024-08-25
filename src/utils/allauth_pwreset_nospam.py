"""Noop method to disable email sending."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest


def mock_send_unknown_account_email(self, request: HttpRequest, email) -> None:
    # do not send email to unknown accounts, see
    # https://github.com/pennersr/django-allauth/issues/3333
    pass
