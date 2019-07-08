from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save
from .signal_handlers import create_profile, profile_pre_save
import logging

logger = logging.getLogger("bornhack.%s" % __name__)


class ProfilesConfig(AppConfig):
    name = "profiles"

    def ready(self):
        # remember to include a dispatch_uid to prevent signals being called multiple times in certain corner cases
        from django.contrib.auth.models import User

        post_save.connect(
            create_profile, sender=User, dispatch_uid="user_post_save_signal"
        )
        pre_save.connect(
            profile_pre_save,
            sender="profiles.Profile",
            dispatch_uid="profile_pre_save_signal",
        )
