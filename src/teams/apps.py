from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete
from .signal_handlers import teammember_saved, teammember_deleted


class TeamsConfig(AppConfig):
    name = "teams"

    def ready(self):
        # connect the post_save signal, always including a dispatch_uid to prevent it being called multiple times in corner cases
        post_save.connect(
            teammember_saved,
            sender="teams.TeamMember",
            dispatch_uid="teammember_save_signal",
        )
        post_delete.connect(
            teammember_deleted,
            sender="teams.TeamMember",
            dispatch_uid="teammember_save_signal",
        )
