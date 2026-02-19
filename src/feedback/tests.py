from datetime import datetime

from feedback.models import CampFeedback
from utils.tests import BornhackTestBase

class TestFeedbackModel(BornhackTestBase):
    """Test Feedback Model."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        super().setUpTestData()
        cls.feedback = CampFeedback.objects.create(
            camp=cls.camp,
            user=cls.users[0],
            feedback="Test Feedback"
        )

        cls.admin = cls.users["admin"]


    def test_state_of_new_feedback_is_unprocessed(self) -> None:
        """Test the state of a new event feedback."""
        assert self.feedback.state == CampFeedback.StateChoices.UNPROCESSED

    def test_process_feedback_sets_user_and_timestamp(self) -> None:
        """
        Test process_feedback sets the user processing feedback with timestamp.
        """
        self.feedback.process_feedback("reviewed", self.admin)

        assert self.feedback.processed_by is self.admin
        assert isinstance(self.feedback.processed_at, datetime)

    def test_process_feedback_with_non_orga_user_raises_error(self) -> None:
        """
        Test process_feedback raises exception when called with user
        without permission.
        """
        with self.assertRaises(PermissionError):
            self.feedback.process_feedback("reviewed", self.users[1])

    def test_process_feedback_changes_state_to_spam(self) -> None:
        """Test process_feedback changes the state for Feedback to SPAM."""
        self.feedback.process_feedback("spam", self.admin)

        assert self.feedback.state is CampFeedback.StateChoices.SPAM

    def test_process_feedback_changes_state_to_reviewed(self) -> None:
        """Test process_feedback changes the state for Feedback to reviewed."""
        self.feedback.process_feedback("reviewed", self.admin)

        assert self.feedback.state is CampFeedback.StateChoices.REVIEWED

    def test_process_feedback_changes_state_to_unprocessed(self) -> None:
        """
        Test process_feedback changes the state for Feedback to unprocessed
        and changing the `processed_by` and `processed_at` to None.
        """
        self.feedback.process_feedback("spam", self.admin)
        self.feedback.process_feedback("unprocessed", self.admin)

        assert self.feedback.state is CampFeedback.StateChoices.UNPROCESSED
        assert self.feedback.processed_by is None
        assert self.feedback.processed_at is None

    def test_process_feedback_with_unknown_state_raises_error(self) -> None:
        """
        Test process_feedback raises exception when state parameter is unknown.
        """
        with self.assertRaises(ValueError):
            self.feedback.process_feedback("unknown", self.admin)

    def test_process_feedback_state_is_case_insensitive(self) -> None:
        """
        Test process_feedback handle state as case_insensitive.
        """
        self.feedback.process_feedback("SPAM", self.admin)

        assert self.feedback.state is CampFeedback.StateChoices.SPAM

