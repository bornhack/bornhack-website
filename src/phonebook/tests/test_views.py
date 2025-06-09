"""Tests for Phonebook views."""

from __future__ import annotations

from bs4 import BeautifulSoup
from django.urls import reverse

from phonebook.models import DectRegistration
from utils.tests import BornhackTestBase


class TestPhonebookViews(BornhackTestBase):
    """Test Phonebook view."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Add test data."""
        # first add users and other basics
        super().setUpTestData()
        # then create some albums
        DectRegistration(
            camp=cls.camp,
            user=cls.users[0],
            number="1234",
            letters="",
            description="1234 nr test",
            publish_in_phonebook=True,
            ipei=[],
        ).save()
        DectRegistration(
            camp=cls.camp,
            user=cls.users[0],
            number="",
            letters="SHIT",
            description="SHIT nr test",
            publish_in_phonebook=True,
            ipei=[],
        ).save()
        DectRegistration(
            camp=cls.camp,
            user=cls.users[0],
            number="",
            letters="HIDE",
            description="HIDE nr test",
            publish_in_phonebook=False,
            ipei=[],
        ).save()

    def test_phonebook_list_view(self) -> None:
        """Test the basics of the phonebook list view."""
        url = reverse("phonebook:list", kwargs={"camp_slug": self.camp.slug})

        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 2, "phonebook list does not return 2 entries")

    def test_dect_registration_list_view(self) -> None:
        """Test the basics of the dect registrations list view."""
        url = reverse("phonebook:dectregistration_list", kwargs={"camp_slug": self.camp.slug})
        self.client.force_login(self.users[0]) 

        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 3, "dect registration list does not return 2 registrations")

    def test_dect_registration_create_view(self) -> None:
        """Test the basics of the dect registrations create view."""
        self.client.force_login(self.users[0]) 

        url = reverse("phonebook:dectregistration_create", kwargs={"camp_slug": self.camp.slug})

        # Test creating 9999
        response = self.client.post(
            path=url,
            data={
                "number": "9999",
                "letters": "",
                "description": "Test number",
                "publish_in_phonebook": False,
                "ipei": "00DEADBEEF",
            },
            follow=True,
        )
        assert response.status_code == 200

        # Test if the registration shows up
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 4, "dect registration create number failed")

        # Test Named number
        response = self.client.post(
            path=url,
            data={
                "number": "",
                "letters": "INFO",
                "description": "INFO Test number",
                "publish_in_phonebook": True,
                "ipei": "03562 0900848",
            },
            follow=True,
        )
        assert response.status_code == 200

        # Test if the registration shows up
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 5, "dect registration create INFO failed")

        # Test duplicated number
        response = self.client.post(
            path=url,
            data={
                "number": "",
                "letters": "INFO",
                "description": "INFO Test number",
                "publish_in_phonebook": True,
                "ipei": "",
            },
            follow=True,
        )
        assert response.status_code == 200

        # Test if the registration does not show up
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select(".invalid-feedback")
        self.assertEqual(len(rows), 1, "dect registration create duplicate failed")

        # Test duplicated IPEI
        response = self.client.post(
            path=url,
            data={
                "number": "",
                "letters": "FOOD",
                "description": "FOOD Test number",
                "publish_in_phonebook": True,
                "ipei": "03562 0900848",
            },
            follow=True,
        )
        assert response.status_code == 200

        # Test if the registration does not show up
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select(".invalid-feedback")
        self.assertEqual(len(rows), 1, "dect registration create duplicate ipei failed")

        # Test total numbers in the phonebook (3)
        url = reverse("phonebook:list", kwargs={"camp_slug": self.camp.slug})
        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("table#main_table > tbody > tr")
        self.assertEqual(len(rows), 3, "phonebook list does not return 3 entries after create")
