"""Factories for bootstrapping the events application."""

from __future__ import annotations

import logging

import factory
import pytz
from django.contrib.auth.models import User
from faker import Faker

from program.models import EventProposal
from program.models import SpeakerProposal
from program.models import Url
from program.models import UrlType
from utils.bootstrap.functions import output_fake_description
from utils.bootstrap.functions import output_fake_md_description

fake = Faker()
tz = pytz.timezone("Europe/Copenhagen")
logger = logging.getLogger(f"bornhack.{__name__}")

class SpeakerProposalFactory(factory.django.DjangoModelFactory):
    """Factory for speaker proposals."""

    class Meta:
        """Meta."""

        model = SpeakerProposal

    name = factory.Sequence(lambda _: fake.unique.name()) 
    email = factory.Sequence(lambda _: fake.unique.email())
    biography = output_fake_md_description()
    submission_notes = factory.Iterator(["", output_fake_description()])
    needs_oneday_ticket = factory.Iterator([True, False])


class EventProposalFactory(factory.django.DjangoModelFactory):
    """Factory for event proposals."""

    class Meta:
        """Meta."""

        model = EventProposal

    user = factory.Iterator(User.objects.all())
    title = factory.Faker("sentence")
    abstract = output_fake_md_description()
    allow_video_recording = factory.Iterator([True, True, True, False])
    allow_video_streaming = factory.Iterator([True, True, True, False])
    submission_notes = factory.Iterator(["", output_fake_description()])
    use_provided_speaker_laptop = factory.Iterator([True, False])


class EventProposalUrlFactory(factory.django.DjangoModelFactory):
    """Factory for event proposal urls."""

    class Meta:
        """Meta."""

        model = Url

    url = factory.Faker("url")
    url_type = factory.Iterator(UrlType.objects.all())


class SpeakerProposalUrlFactory(factory.django.DjangoModelFactory):
    """Factory for speaker proposal urls."""

    class Meta:
        """Meta."""

        model = Url

    url = factory.Faker("url")
    url_type = factory.Iterator(UrlType.objects.all())
