from django.apps import AppConfig
from django.db.models.signals import post_save
from .signal_handlers import add_responsible_email

class TeamsConfig(AppConfig):
    name = 'teams'

    def ready(self):
        # connect the post_save signal, always including a dispatch_uid to prevent it being called multiple times in corner cases
        post_save.connect(add_responsible_email, sender='teams.TeamMember', dispatch_uid='teammember_save_signal')

