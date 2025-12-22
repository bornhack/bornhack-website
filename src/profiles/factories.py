"""Factories for bootstrapping profiles application."""

from __future__ import annotations

import logging

import factory
import pytz
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from faker import Faker

from profiles.models import Profile

fake = Faker()
tz = pytz.timezone("Europe/Copenhagen")
logger = logging.getLogger(f"bornhack.{__name__}")

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
        skip_postgeneration_save = True

    profile = factory.RelatedFactory(ProfileFactory, "user")


class EmailAddressFactory(factory.django.DjangoModelFactory):
    """Factory for email address."""

    class Meta:
        """Meta."""

        model = EmailAddress

    primary = False
    verified = True
