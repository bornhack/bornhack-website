"""Noop method to disable email sending."""


def mock_send_unknown_account_email(self, request, email):
    # do not send email to unknown accounts, see
    # https://github.com/pennersr/django-allauth/issues/3333
    pass
