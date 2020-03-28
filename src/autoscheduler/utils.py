from .models import AutoSchedule


def create_autoschedule(camp, event_type):
    """ Create a new AutoSchedule and related objects """
    schedule = AutoSchedule.objects.create(camp=camp, event_type=event_type)
    schedule.create_autoscheduler_objects()
    schedule.apply()
