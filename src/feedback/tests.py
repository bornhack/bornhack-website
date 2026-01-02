from feedback.models import Feedback
from utils.tests import BornhackTestBase

class TestFeedbackModel(BornhackTestBase):
    """Test Feedback Model."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        super().setUpTestData()
        cls.feedback = Feedback.objects.create(
            camp=cls.camp,
            user=cls.users[0],
            feedback="Test Feedback"
        )

    def test_state_of_new_feedback_is_unprocessed(self) -> None:
        """Test the state of a new event feedback."""
        assert self.feedback.state == Feedback.StateChoices.UNPROCESSED

