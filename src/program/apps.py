from django.apps import AppConfig
from django.db.models.signals import m2m_changed, pre_save


class ProgramConfig(AppConfig):
    name = "program"

    def ready(self):
        from .models import Speaker
        from .signal_handlers import (
            check_speaker_event_camp_consistency,
            check_speaker_camp_change,
        )

        m2m_changed.connect(
            check_speaker_event_camp_consistency, sender=Speaker.events.through
        )
        pre_save.connect(check_speaker_camp_change, sender=Speaker)
