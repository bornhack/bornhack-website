
from django.urls import reverse
from feedback.models import Feedback
from utils.tests import BornhackTestBase


class TestEventFeedbackProcessView(BornhackTestBase):
    """Test EventFeedbackProcessView."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        super().setUpTestData()
        cls.feedback = Feedback.objects.create(
            camp=cls.camp,
            user=cls.users[0],
            feedback="Test Feedback"
        )

        cls.admin = cls.users["admin"]
        cls.kwargs = {
            "camp_slug": cls.camp.slug,
            "pk": cls.feedback.pk,
            "state": "reviewed"
        }

    def test_admin_processing_feedback_as_reviewed(self) -> None:
        """Test admin user processing feedback as reviewed."""
        self.client.force_login(self.admin)
        url = reverse("backoffice:feedback_process", kwargs=self.kwargs)

        self.client.post(url)
        self.feedback.refresh_from_db()

        assert self.feedback.state == Feedback.StateChoices.REVIEWED

    def test_admin_processing_feedback_as_spam(self) -> None:
        """Test admin user processing feedback as spam."""
        self.client.force_login(self.admin)
        self.kwargs.update({"state": "spam"})
        url = reverse("backoffice:feedback_process", kwargs=self.kwargs)

        self.client.post(url)
        self.feedback.refresh_from_db()

        assert self.feedback.state == Feedback.StateChoices.SPAM

