"""Noop method to disable email sending."""

from __future__ import annotations


def mock_send_unknown_account_email(self, request, email) -> None:
    # do not send email to unknown accounts, see
    # https://github.com/pennersr/django-allauth/issues/3333
    pass
