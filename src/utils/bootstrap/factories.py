"""Factories for bootstrapping the application."""

from __future__ import annotations

import logging
import random

import factory
import pytz
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from faker import Faker

from camps.models import Camp
from economy.models import Chain
from economy.models import Credebtor
from economy.models import Expense
from economy.models import Revenue
from profiles.models import Profile
from program.models import EventProposal
from program.models import SpeakerProposal
from program.models import Url
from program.models import UrlType
from teams.models import Team
from utils.slugs import unique_slugify

from .functions import output_fake_description
from .functions import output_fake_md_description

fake = Faker()
tz = pytz.timezone("Europe/Copenhagen")
logger = logging.getLogger(f"bornhack.{__name__}")


class ChainFactory(factory.django.DjangoModelFactory):
    """Factory for creating chains."""

    class Meta:
        """Meta."""

        model = Chain

    name = factory.Faker("company")
    slug = factory.LazyAttribute(
        lambda f: unique_slugify(
            f.name,
            Chain.objects.all().values_list("slug", flat=True),
        ),
    )


class CredebtorFactory(factory.django.DjangoModelFactory):
    """Factory for creating Creditors and debitors."""

    class Meta:
        """Meta."""

        model = Credebtor

    chain = factory.SubFactory(ChainFactory)
    name = factory.Faker("company")
    slug = factory.LazyAttribute(
        lambda f: unique_slugify(
            f.name,
            Credebtor.objects.all().values_list("slug", flat=True),
        ),
    )
    address = factory.Faker("address", locale="dk_DK")
    notes = factory.Faker("text")


class ExpenseFactory(factory.django.DjangoModelFactory):
    """Factory for creating expense data."""

    class Meta:
        """Meta."""

        model = Expense

    camp = factory.Faker("random_element", elements=Camp.objects.all())
    creditor = factory.Faker("random_element", elements=Credebtor.objects.all())
    user = factory.Faker("random_element", elements=User.objects.all())
    amount = factory.Faker("random_int", min=20, max=20000)
    description = factory.Faker("text")
    paid_by_bornhack = factory.Faker("random_element", elements=[True, True, False])
    invoice = factory.django.ImageField(
        color=random.choice(["#ff0000", "#00ff00", "#0000ff"]),  # noqa: S311
    )
    invoice_date = factory.Faker("date")
    responsible_team = factory.Faker("random_element", elements=Team.objects.all())
    approved = factory.Faker("random_element", elements=[True, True, False])
    notes = factory.Faker("text")


class RevenueFactory(factory.django.DjangoModelFactory):
    """Factory for creating revenue data."""

    class Meta:
        """Meta."""

        model = Revenue

    camp = factory.Faker("random_element", elements=Camp.objects.all())
    debtor = factory.Faker("random_element", elements=Credebtor.objects.all())
    user = factory.Faker("random_element", elements=User.objects.all())
    amount = factory.Faker("random_int", min=20, max=20000)
    description = factory.Faker("text")
    invoice = factory.django.ImageField(
        color=random.choice(["#ff0000", "#00ff00", "#0000ff"]),  # noqa: S311
    )
    invoice_date = factory.Faker("date")
    responsible_team = factory.Faker("random_element", elements=Team.objects.all())
    approved = factory.Faker("random_element", elements=[True, True, False])
    notes = factory.Faker("text")


class ProfileFactory(factory.django.DjangoModelFactory):
    """Factory for creating user profiles."""

    class Meta:
        """Meta."""

        model = Profile

    user = factory.SubFactory("self.UserFactory", profile=None)
    name = factory.Faker("name")
    description = factory.Faker("text")
    public_credit_name = factory.Faker("name")
    public_credit_name_approved = True


@factory.django.mute_signals(post_save)
class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating a User."""

    class Meta:
        """Meta."""

        model = User

    profile = factory.RelatedFactory(ProfileFactory, "user")


class EmailAddressFactory(factory.django.DjangoModelFactory):
    """Factory for email address."""

    class Meta:
        """Meta."""

        model = EmailAddress

    primary = False
    verified = True


class SpeakerProposalFactory(factory.django.DjangoModelFactory):
    """Factory for speaker proposals."""

    class Meta:
        """Meta."""

        model = SpeakerProposal

    name = factory.Faker("name")
    email = factory.Faker("email")
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
