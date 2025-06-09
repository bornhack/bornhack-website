from __future__ import annotations

import datetime

from django.test import TestCase
from django.urls import reverse


class CampMenuTest(TestCase):
    def test_this_year_shown_on_homepage(self):
        """By March, the current year's camp should be on the homepage."""
        response = self.client.get(
            "/news/",
        )  # The tests don't work with / because of the camp dispatcher.
        year = (datetime.date.today() - datetime.timedelta(days=59)).year
        href = reverse("camp_detail", kwargs={"camp_slug": f"bornhack-{year}"})
        assert href in response.content.decode("utf-8")
