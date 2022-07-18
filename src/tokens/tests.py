from django.test import Client
from django.test import TestCase
from django.urls import reverse


class CampMenuTest(TestCase):
    def test_this_year_shown_on_homepage(self):
        """By March, the current year's camp should be on the homepage."""
        c = Client()
        response = c.get("/bornhack-2022/")
        assert b"/token/" in response.content
