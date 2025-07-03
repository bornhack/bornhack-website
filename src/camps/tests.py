from __future__ import annotations

import datetime

from django.test import TestCase
from django.urls import reverse

from tickets.models import ShopTicket
from tickets.models import SponsorTicket
from tickets.models import PrizeTicket
from utils.tests import BornhackTestBase

class CampMenuTest(TestCase):
    def test_this_year_shown_on_homepage(self):
        """By March, the current year's camp should be on the homepage."""
        response = self.client.get(
            "/news/",
        )  # The tests don't work with / because of the camp dispatcher.
        year = (datetime.date.today() - datetime.timedelta(days=59)).year
        href = reverse("camp_detail", kwargs={"camp_slug": f"bornhack-{year}"})
        assert href in response.content.decode("utf-8")


class TestCampModel(BornhackTestBase):
    """Tests for the Camp model"""

    def setUp(self) -> None:
        super().setUp()
        self.full_week_adults = {
            "shop_tickets": (
                ShopTicket.objects.filter(ticket_type__camp=self.camp)
                .filter(ticket_type=self.camp.ticket_type_full_week_adult)
            ),
            "sponsor_tickets": (
                SponsorTicket.objects.filter(ticket_type__camp=self.camp)
                .filter(ticket_type=self.camp.ticket_type_full_week_adult)
            ),
        }
        self.full_week_children = (
            ShopTicket.objects.filter(ticket_type__camp=self.camp)
            .filter(ticket_type=self.camp.ticket_type_full_week_child)
        )

    def test_checked_in_full_week_adults(self) -> None:
        """Test the return value of checked in full week adults"""
        tickets = [
            self.full_week_adults["shop_tickets"][0],
            self.full_week_adults["sponsor_tickets"][0],
        ]
        for ticket in tickets:
            ticket.used_at = self.camp.camp.lower
            ticket.save()

        assert self.camp.checked_in_full_week_adults == 2

    def test_checked_in_full_week_children(self) -> None:
        """Test the return value of checked in full week children"""
        ticket1 = self.full_week_children[0]
        ticket1.used_at = self.camp.camp.lower
        ticket1.save()
        assert self.camp.checked_in_full_week_children == 1

