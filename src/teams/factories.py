import factory

from .models import Team


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    camp = factory.SubFactory("camps.factories.CampFactory")
    name = factory.Faker("name")
    description = factory.Faker("paragraph")
