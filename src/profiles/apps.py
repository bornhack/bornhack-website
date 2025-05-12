from __future__ import annotations

import logging

from allauth.account.signals import user_logged_in
from django.apps import AppConfig
from django.db.models.signals import post_save
from django.db.models.signals import pre_save

from .signal_handlers import create_profile
from .signal_handlers import profile_pre_save
from .signal_handlers import set_session_on_login

logger = logging.getLogger(f"bornhack.{__name__}")


class ProfilesConfig(AppConfig):
    name = "profiles"

    def ready(self) -> None:
        # remember to include a dispatch_uid to prevent signals being called multiple times in certain corner cases
        from django.contrib.auth.models import User

        post_save.connect(
            create_profile,
            sender=User,
            dispatch_uid="user_post_save_signal",
        )
        pre_save.connect(
            profile_pre_save,
            sender="profiles.Profile",
            dispatch_uid="profile_pre_save_signal",
        )
        user_logged_in.connect(
            set_session_on_login,
            sender=User,
            dispatch_uid="profile_set_session_on_login_signal",
        )
