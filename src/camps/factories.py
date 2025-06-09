from __future__ import annotations

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from psycopg2._range import DateTimeTZRange


class CampFactory(DjangoModelFactory):
    class Meta:
        model = "camps.Camp"

    read_only = False

    title = factory.Faker("word")
    tagline = factory.Faker("sentence")
    slug = factory.Faker("slug")
    shortslug = factory.Faker("slug")

    buildup = factory.LazyFunction(
        lambda: DateTimeTZRange(
            lower=timezone.now() - timezone.timedelta(days=3),
            upper=timezone.now() - timezone.timedelta(hours=1),
        ),
    )

    camp = factory.LazyFunction(
        lambda: DateTimeTZRange(
            lower=timezone.now(),
            upper=timezone.now() + timezone.timedelta(days=8),
        ),
    )

    teardown = factory.LazyFunction(
        lambda: DateTimeTZRange(
            lower=timezone.now() + timezone.timedelta(days=8, hours=1),
            upper=timezone.now() + timezone.timedelta(days=11),
        ),
    )

    colour = factory.Faker("hex_color")
