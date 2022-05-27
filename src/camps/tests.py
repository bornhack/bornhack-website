import datetime

from django.test import Client, TestCase
from django.urls import reverse


class CampDisplayTest(TestCase):
    def test_this_year_shown_on_homepage(self):
        """Starting in March year, current year's camp should be on the homepage."""
        c = Client()
        response = c.get('/')
        year = (datetime.date.today() - datetime.timedelta(days=59)).year
        href = reverse("camp_detail", kwargs={"camp_slug": f'bornhack-{year}'})
        assert href in response.text
