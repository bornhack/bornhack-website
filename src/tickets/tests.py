from django.test import TestCase

from .factories import TicketTypeFactory
from .models import ShopTicket
from shop.factories import OrderProductRelationFactory


class TicketTests(TestCase):
    def test_correct_token_and_badge_token_are_different(self):
        ticket_type = TicketTypeFactory()
        opr = OrderProductRelationFactory()
        shop_ticket = ShopTicket.objects.create(
            ticket_type=ticket_type,
            product=opr.product,
            opr=opr,
        )

        self.assertNotEqual(shop_ticket.token, shop_ticket.badge_token)
        self.assertEqual(shop_ticket.token, shop_ticket._get_token())
        self.assertEqual(shop_ticket.badge_token, shop_ticket._get_badge_token())
