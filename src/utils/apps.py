from __future__ import annotations

from django.apps import AppConfig

from utils.allauth_pwreset_nospam import mock_send_unknown_account_email


class UtilsConfig(AppConfig):
    name = "utils"

    def ready(self) -> None:
        """Do stuff after apps are loaded."""
        # monkeypatch password reset form
        from allauth.account.forms import ResetPasswordForm

        ResetPasswordForm._send_unknown_account_mail = mock_send_unknown_account_email
