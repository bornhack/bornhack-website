from django.apps import AppConfig
from django.db.models.signals import m2m_changed, post_save, pre_save


class ProgramConfig(AppConfig):
    name = "program"

    def ready(self):
        from .models import Speaker, EventInstance
        from .signal_handlers import (
            check_speaker_event_camp_consistency,
            check_speaker_camp_change,
            eventinstance_pre_save,
            eventinstance_post_save,
        )

        m2m_changed.connect(
            check_speaker_event_camp_consistency, sender=Speaker.events.through
        )

        pre_save.connect(check_speaker_camp_change, sender=Speaker)
        pre_save.connect(eventinstance_pre_save, sender=EventInstance)

        post_save.connect(eventinstance_post_save, sender=EventInstance)
