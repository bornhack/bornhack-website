from django.core.exceptions import ValidationError

def check_speaker_event_camp_consistency(sender, instance, **kwargs):
    if kwargs['action'] == 'pre_add':
        for pk in kwargs['pk_set']:
            # check if this event belongs to a different event than the speaker does
            from program.models import Event
            event = Event.objects.get(id=pk)
            if event.camp != instance.camp:
                raise ValidationError({'events': 'One or more events belong to a different camp (%s) than the speaker (%s) does' % (event.camp, instance.camp)})

def check_speaker_camp_change(sender, instance, **kwargs):
    if instance.pk:
        for event in instance.events.all():
            if event.camp != instance.camp:
                raise ValidationError({'camp': 'You cannot change the camp a speaker belongs to if the speaker is associated with one or more events.'})

