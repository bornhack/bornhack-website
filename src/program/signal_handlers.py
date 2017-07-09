from django.core.exceptions import ValidationError


def check_speaker_event_camp_consistency(sender, instance, **kwargs):
    if kwargs['action'] == 'pre_add':
        # loop over speakers being added to this event
        for pk in kwargs['pk_set']:
            # check if this speaker belongs to a different event than the event does
            from program.models import Speaker
            speaker = Speaker.objects.get(id=pk)
            if speaker.camp != instance.camp:
                raise ValidationError({'speakers': 'The speaker (%s) belongs to a different camp (%s) than the event does (%s)' % (speaker, speaker.camp, instance.camp)})


def check_speaker_camp_change(sender, instance, **kwargs):
    if instance.pk:
        for event in instance.events.all():
            if event.camp != instance.camp:
                raise ValidationError({'camp': 'You cannot change the camp a speaker belongs to if the speaker is associated with one or more events.'})

