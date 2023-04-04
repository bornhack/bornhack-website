import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from psycopg2.extras import DateTimeTZRange

from utils.factories import UserFactory


class ProductCategoryFactory(DjangoModelFactory):
    class Meta:
        model = "shop.ProductCategory"

    name = factory.Faker("word")


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = "shop.Product"

    name = factory.Faker("word")
    slug = factory.Faker("slug")
    category = factory.SubFactory(ProductCategoryFactory)
    description = factory.Faker("paragraph")
    price = factory.Faker("pyint")
    available_in = factory.LazyFunction(
        lambda: DateTimeTZRange(
            lower=timezone.now(),
            upper=timezone.now() + timezone.timedelta(31),
        ),
    )
    ticket_type = factory.SubFactory("tickets.factories.TicketTypeFactory")


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = "shop.Order"

    user = factory.SubFactory(UserFactory)


class OrderProductRelationFactory(DjangoModelFactory):
    class Meta:
        model = "shop.OrderProductRelation"

    product = factory.SubFactory(ProductFactory)
    order = factory.SubFactory(OrderFactory)
    quantity = 1
