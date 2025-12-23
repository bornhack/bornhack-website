from __future__ import annotations

import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from sponsors.models import Sponsor
from tickets.models import PrizeTicket
from tickets.models import ShopTicket
from tickets.models import SponsorTicket
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
        self.full_week_adults = {  # All tickets are created by bootstrapping
            "shop_tickets": (
                ShopTicket.objects.filter(
                    ticket_type=self.camp.ticket_type_full_week_adult,
                )
            ),
            "sponsor_tickets": (
                SponsorTicket.objects.filter(
                    ticket_type=self.camp.ticket_type_full_week_adult,
                )
            ),
            "prize_tickets": (
                PrizeTicket.objects.filter(
                    ticket_type=self.camp.ticket_type_full_week_adult,
                )
            ),
        }
        self.full_week_children = (  # ShopTickets created by bootstrapping
            ShopTicket.objects.filter(
                ticket_type=self.camp.ticket_type_full_week_child,
            )
        )
        self.one_day_adults = (  # ShopTickets created by bootstrapping
            ShopTicket.objects.filter(
                ticket_type=self.camp.ticket_type_one_day_adult,
            )
        )
        self.one_day_children = (  # ShopTickets created by bootstrapping
            ShopTicket.objects.filter(
                ticket_type=self.camp.ticket_type_one_day_child,
            )
        )

    def test_checked_in_full_week_adults_all_ticket_types(self) -> None:
        """Test the return value of checked in full week adults for all tickets"""
        tickets = [
            self.full_week_adults["shop_tickets"][0],
            self.full_week_adults["sponsor_tickets"][0],
            self.full_week_adults["prize_tickets"][0],
        ]
        for ticket in tickets:
            ticket.used_at = self.camp.camp.lower
            ticket.save()

        assert self.camp.checked_in_full_week_adults == 3

    def test_checked_in_full_week_children_shop_tickets(self) -> None:
        """Test the return value of checked in full week children with shop ticket"""
        ticket = self.full_week_children[0]
        ticket.used_at = self.camp.camp.lower
        ticket.save()
        assert self.camp.checked_in_full_week_children == 1

    def test_checked_in_full_week_children_with_sponsor_ticket(self) -> None:
        """Test the return value of checked in full week children with sponsor ticket"""
        sponsor = Sponsor.objects.all().first()
        SponsorTicket.objects.create(
            sponsor=sponsor,
            ticket_type=self.camp.ticket_type_full_week_child,
            used_at=self.camp.camp.lower,
        )
        assert self.camp.checked_in_full_week_children == 1

    def test_checked_in_full_week_children_with_prize_ticket(self) -> None:
        """Test the return value of checked in full week children with prize ticket"""
        PrizeTicket.objects.create(
            user=self.users[0],
            ticket_type=self.camp.ticket_type_full_week_child,
            comment="Prize winner",
            used_at=self.camp.camp.lower,
        )
        assert self.camp.checked_in_full_week_children == 1

    def test_checked_in_one_day_adults(self) -> None:
        """Test the return value of checked in one day adults today"""
        for ticket in self.one_day_adults[:2]:
            ticket.used_at = timezone.localtime()
            ticket.save()

        assert self.camp.checked_in_one_day_adults == 2

    def test_checked_in_one_day_adults_with_sponsor_ticket(self) -> None:
        """Test the return value of checked in one day adults
        with sponsor ticket today
        """
        sponsor = Sponsor.objects.all().first()
        SponsorTicket.objects.create(
            sponsor=sponsor,
            ticket_type=self.camp.ticket_type_one_day_adult,
            used_at=timezone.localtime(),
        )

        assert self.camp.checked_in_one_day_adults == 1

    def test_checked_in_one_day_adults_with_prize_ticket(self) -> None:
        """Test the return value of checked in one day adults
        with prize ticket today
        """
        PrizeTicket.objects.create(
            user=self.users[0],
            ticket_type=self.camp.ticket_type_one_day_adult,
            comment="Prize winner",
            used_at=timezone.localtime(),
        )

        assert self.camp.checked_in_one_day_adults == 1

    def test_checked_in_one_day_adults_timing(self) -> None:
        """Test check in before 06 yesterday don't count"""
        valid = self.one_day_adults[0]
        valid.used_at = timezone.localtime()
        valid.save()

        not_valid = self.one_day_adults[1]
        not_valid.used_at = timezone.localtime() - timezone.timedelta(days=2)
        not_valid.save()

        assert self.camp.checked_in_one_day_adults == 1

    def test_checked_in_one_day_children(self) -> None:
        """Test the return value of checked in one day children today"""
        for ticket in self.one_day_children[:2]:
            ticket.used_at = timezone.localtime()
            ticket.save()

        assert self.camp.checked_in_one_day_children == 2

    def test_checked_in_one_day_children_with_sponsor_ticket(self) -> None:
        """Test the return value of checked in one day children
        with sponsor ticket today
        """
        sponsor = Sponsor.objects.all().first()
        SponsorTicket.objects.create(
            sponsor=sponsor,
            ticket_type=self.camp.ticket_type_one_day_child,
            used_at=timezone.localtime(),
        )

        assert self.camp.checked_in_one_day_children == 1

    def test_checked_in_one_day_children_with_prize_ticket(self) -> None:
        """Test the return value of checked in one day children
        with prize ticket today
        """
        PrizeTicket.objects.create(
            user=self.users[0],
            ticket_type=self.camp.ticket_type_one_day_child,
            comment="Prize winner",
            used_at=timezone.localtime(),
        )

        assert self.camp.checked_in_one_day_children == 1

    def test_checked_in_one_day_children_timing(self) -> None:
        """Test check in before 06 yesterday don't count"""
        valid = self.one_day_children[0]
        valid.used_at = timezone.localtime()
        valid.save()

        not_valid = self.one_day_children[1]
        not_valid.used_at = timezone.localtime() - timezone.timedelta(days=2)
        not_valid.save()

        assert self.camp.checked_in_one_day_children == 1

    def test_participant_count(self) -> None:
        """Test the count of all participants"""
        adult_full_week = self.full_week_adults["shop_tickets"][0]
        adult_full_week.used_at = self.camp.camp.lower
        adult_full_week.save()

        child_full_week = self.full_week_children[0]
        child_full_week.used_at = self.camp.camp.lower
        child_full_week.save()

        adult_one_day = self.one_day_adults[0]
        adult_one_day.used_at = timezone.localtime()
        adult_one_day.save()

        child_one_day = self.one_day_children[0]
        child_one_day.used_at = timezone.localtime()
        child_one_day.save()

        assert self.camp.participant_count == 4
