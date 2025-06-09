from __future__ import annotations

import factory
from factory.django import DjangoModelFactory


class TicketTypeFactory(DjangoModelFactory):
    class Meta:
        model = "tickets.TicketType"

    name = factory.Faker("sentence")
    camp = factory.SubFactory("camps.factories.CampFactory")


class ShopTicketFactory(DjangoModelFactory):
    class Meta:
        model = "tickets.ShopTicket"

    ticket_type = factory.SubFactory(TicketTypeFactory)
