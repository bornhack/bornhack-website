from django.urls import reverse

from utils.tests import BornhackTestBase
from program.models import Event

class TestFeedbackCreateView(BornhackTestBase):
    """Test FeedbackCreateView"""

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        super().setUpTestData()
        cls.bootstrap.create_camp_proposals(cls.camp, cls.bootstrap.event_types)

    def test_create_feedback_requires_login(self) -> None:
        """Test creating feedback for an event requires user to be signed in"""
        event = Event.objects.all().first()
        kwargs = {"camp_slug": self.camp.slug, "event_slug": event.slug}
        url = reverse("program:event_feedback_create", kwargs=kwargs)
        expected = reverse("program:event_detail", kwargs=kwargs)

        response = self.client.get(url)

        self.assertRedirects(response, expected)

