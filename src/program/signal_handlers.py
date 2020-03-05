import logging

from django.core.exceptions import ValidationError

from .email import add_event_scheduled_email

logger = logging.getLogger("bornhack.%s" % __name__)


def check_speaker_event_camp_consistency(sender, instance, **kwargs):
    if kwargs["action"] == "pre_add":
        from program.models import Speaker, Event

        if isinstance(instance, Event):
            # loop over speakers being added to this event
            for pk in kwargs["pk_set"]:
                # check if this speaker belongs to a different Camp than the event does
                speaker = Speaker.objects.get(id=pk)
                if speaker.camp != instance.camp:
                    raise ValidationError(
                        {
                            "speakers": "The speaker (%s) belongs to a different camp (%s) than the event does (%s)"
                            % (speaker, speaker.camp, instance.camp)
                        }
                    )
        elif isinstance(instance, Speaker):
            # loop over events being added to this speaker
            for pk in kwargs["pk_set"]:
                # check if this event belongs to a different Camp than the speaker does
                event = Event.objects.get(id=pk)
                if event.camp != instance.camp:
                    raise ValidationError(
                        {
                            "events": f"The event ({event}) belongs to a different camp ({event.camp}) than the speaker does ({instance.camp})"
                        }
                    )


def check_speaker_camp_change(sender, instance, **kwargs):
    if instance.pk:
        for event in instance.events.all():
            if event.camp != instance.camp:
                raise ValidationError(
                    {
                        "camp": "You cannot change the camp a speaker belongs to if the speaker is associated with one or more events."
                    }
                )


def eventinstance_pre_save(sender, instance, **kwargs):
    """ Save the old instance.when value so we can later determine if it changed """
    try:
        # get the old instance from the database, if we have one
        instance.old_when = sender.objects.get(pk=instance.pk).when
    except sender.DoesNotExist:
        # nothing found in the DB with this pk, this is a new eventinstance
        instance.old_when = instance.when


def eventinstance_post_save(sender, instance, created, **kwargs):
    """ Send an email if this is a new eventinstance, or if the "when" field changed """
    if created:
        add_event_scheduled_email(eventinstance=instance, action="scheduled")
    else:
        if instance.old_when != instance.when:
            # date/time for this eventinstance changed, send a rescheduled email
            add_event_scheduled_email(eventinstance=instance, action="rescheduled")
