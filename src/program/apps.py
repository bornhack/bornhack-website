from django.apps import AppConfig
from django.db.models.signals import m2m_changed
from django.db.models.signals import post_save


class ProgramConfig(AppConfig):
    name = "program"

    def ready(self):
        from .models import EventSession, Speaker
        from .signal_handlers import (
            check_speaker_event_camp_consistency,
            event_session_post_save,
        )

        m2m_changed.connect(
            check_speaker_event_camp_consistency,
            sender=Speaker.events.through,
        )

        post_save.connect(event_session_post_save, sender=EventSession)
