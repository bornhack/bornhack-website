import logging

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings

from .email import add_new_speakerproposal_email, add_new_eventproposal_email
from .models import EventProposal, SpeakerProposal, UserSubmittedModel
from ircbot.models import OutgoingIrcMessage
logger = logging.getLogger("bornhack.%s" % __name__)


def check_speaker_event_camp_consistency(sender, instance, **kwargs):
    if kwargs['action'] == 'pre_add':
        from program.models import Speaker, Event
        if isinstance(instance, Event):
            # loop over speakers being added to this event
            for pk in kwargs['pk_set']:
                # check if this speaker belongs to a different Camp than the event does
                speaker = Speaker.objects.get(id=pk)
                if speaker.camp != instance.camp:
                    raise ValidationError({'speakers': 'The speaker (%s) belongs to a different camp (%s) than the event does (%s)' % (speaker, speaker.camp, instance.camp)})
        elif isinstance(instance, Speaker):
            # loop over events being added to this speaker
            for pk in kwargs['pk_set']:
                # check if this event belongs to a different Camp than the speaker does
                event = Event.objects.get(id=pk)
                if event.camp != instance.camp:
                    raise ValidationError({'events': 'The event (%s) belongs to a different camp (%s) than the event does (%s)' % (event, event.camp, instance.camp)})


def check_speaker_camp_change(sender, instance, **kwargs):
    if instance.pk:
        for event in instance.events.all():
            if event.camp != instance.camp:
                raise ValidationError({'camp': 'You cannot change the camp a speaker belongs to if the speaker is associated with one or more events.'})


# pre_save signal that notifies if a proposal changes status from draft to
# pending i.e. is submitted.
def notify_proposal_submitted(sender, instance, **kwargs):
    try:
        original = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return False

    target = settings.IRCBOT_CHANNELS['orga'] if 'orga' in settings.IRCBOT_CHANNELS else settings.IRCBOT_CHANNELS['default']

    if original.proposal_status == UserSubmittedModel.PROPOSAL_DRAFT and instance.proposal_status == UserSubmittedModel.PROPOSAL_PENDING:
        if isinstance(instance, EventProposal):
            if not add_new_eventproposal_email(instance):
                logger.error(
                    'Error adding event proposal email to outgoing queue for {}'.format(instance)
                )
            OutgoingIrcMessage.objects.create(
                target=target,
                message="New event proposal: {} - https://bornhack.dk/admin/program/eventproposal/{}/change/".format(
                    instance.title,
                    instance.uuid
                ),
                timeout=timezone.now()+timedelta(minutes=10)
            )

        if isinstance(instance, SpeakerProposal):
            if not add_new_speakerproposal_email(instance):
                logger.error(
                    'Error adding speaker proposal email to outgoing queue for {}'.format(instance)
                )
            OutgoingIrcMessage.objects.create(
                target=target,
                message="New speaker proposal: {} - https://bornhack.dk/admin/program/speakerproposal/{}/change/".format(
                    instance.name,
                    instance.uuid
                ),
                timeout=timezone.now()+timedelta(minutes=10)
            )
