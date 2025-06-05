"""Factories for the teams application."""
from __future__ import annotations

import factory

from .models import Team


class TeamFactory(factory.django.DjangoModelFactory):
    """Team Factory for bootstrapping data."""
    class Meta:
        """Meta."""
        model = Team

    camp = factory.SubFactory("camps.factories.CampFactory")
    name = factory.Faker("name")
    description = factory.Faker("paragraph")
