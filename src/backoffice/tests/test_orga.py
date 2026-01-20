
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

    def test_admin_resets_feedback_as_unprocessed(self) -> None:
        """Test admin user resets feedback as unprocessed."""
        self.client.force_login(self.admin)
        self.kwargs.update({"state": "unprocessed"})
        url = reverse("backoffice:feedback_process", kwargs=self.kwargs)

        self.client.post(url)
        self.feedback.refresh_from_db()

        assert self.feedback.state == Feedback.StateChoices.UNPROCESSED

    def test_bad_request_processing_feedback_with_invalid_state(self) -> None:
        """
        Test processing feedback with invalid state return BadRequest.
        """
        self.client.force_login(self.admin)
        self.kwargs.update({"state": "unknown"})
        url = reverse("backoffice:feedback_process", kwargs=self.kwargs)

        response = self.client.post(url)

        assert response.status_code == 400

    def test_bad_request_requesting_view_with_invalid_state(self) -> None:
        """Test `GET` request to view with invalid state return BadRequest."""
        self.client.force_login(self.admin)
        self.kwargs.update({"state": "unknown"})
        url = reverse("backoffice:feedback_process", kwargs=self.kwargs)

        response = self.client.get(url)

        assert response.status_code == 400
