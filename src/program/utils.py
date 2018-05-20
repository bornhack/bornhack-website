from django.core.exceptions import ImproperlyConfigured
from .forms import *

def get_speakerproposal_form_class(eventtype):
    """
    Return a SpeakerProposal form class suitable for the provided EventType
    """
    if eventtype.name == 'Music Act':
        return MusicSpeakerProposalForm
    elif eventtype.name == 'Talk':
        return TalkSpeakerProposalForm
    elif eventtype.name == 'Workshop':
        return WorkshopSpeakerProposalForm
    elif eventtype.name == 'Lightning Talk':
        return LightningTalkSpeakerProposalForm
    elif eventtype.name == 'Recreational Event':
        return SlackSpeakerProposalForm
    else:
        raise ImproperlyConfigured("Unsupported event type, don't know which form class to use")


def get_eventproposal_form_class(eventtype):
    """
    Return an EventProposal form class suitable for the provided EventType
    """
    if eventtype.name == 'Music Act':
        return MusicEventProposalForm
    elif eventtype.name == 'Talk':
        return TalkEventProposalForm
    elif eventtype.name == 'Workshop':
        return WorkshopEventProposalForm
    elif eventtype.name == 'Lightning Talk':
        return LightningTalkEventProposalForm
    elif eventtype.name == 'Recreational Event':
        return SlackEventProposalForm
    else:
        raise ImproperlyConfigured("Unsupported event type, don't know which form class to use")

