import factory
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    class Meta:
        model = 'auth.User'

    username = factory.Faker('word')
    email = factory.Faker('ascii_email')

