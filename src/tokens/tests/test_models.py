from __future__ import annotations
import uuid

from django.core.exceptions import ValidationError
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from tokens.models import Token
from tokens.models import TokenCategory
from utils.tests import BornhackTestBase


class TestTokenModel(BornhackTestBase):
    """Test Token model."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Add test data."""
        # first add users and other basics
        super().setUpTestData()

        cls.category = TokenCategory.objects.create(
            name="Test",
            description="Test category",
        )

    def create_token(
            self,
            token_str: str|None = None,
            time_range: DateTimeTZRange|None = None
    ) -> Token:
        """Helper method for creating tokens"""
        random_token = str(uuid.uuid4()).replace('-', '')
        return Token.objects.create(
            token=token_str or random_token,
            camp=self.camp,
            category=self.category,
            hint="Test token hint",
            description="Test token description",
            active=True,
            valid_when=time_range
        )

    def test_token_regex_validator_min_length(self) -> None:
        """Test minimum length of token, with regex validator raising exception."""
        with self.assertRaises(ValidationError):
            self.create_token("minlength")

    def test_token_regex_validator_max_length(self) -> None:
        """Test maximum length of token, with regex validator raising exception."""
        with self.assertRaises(ValidationError):
            self.create_token("maxLengthOf32CharactersTokenTests")

    def test_token_regex_validator_invalid_char(self) -> None:
        """Test invalid characters in token, with regex validator raising exception."""
        with self.assertRaises(ValidationError):
            self.create_token("useOfInvalidCharacter+")

        with self.assertRaises(ValidationError):
            self.create_token("-useOfInvalidCharacter")

    def test_creating_valid_tokens(self) -> None:
        """Test valid tokens, with regex validator."""
        self.assertIsInstance(self.create_token("validTokenWith@"), Token)
        self.assertIsInstance(self.create_token("validTokenWith."), Token)
        self.assertIsInstance(self.create_token("validToken12"), Token)
        self.assertIsInstance(
            self.create_token("maxLengthOf32CharactersTokenTest"),
            Token,
        )

    def test_token_is_valid_now_by_time(self) -> None:
        """Test if tokens is valid now by time."""
        now = timezone.now()

        # No `valid_when` datetime.
        token = self.create_token()
        assert token.is_valid_now

        # Not valid yet
        start_date = DateTimeTZRange(lower=now + timezone.timedelta(days=5))
        token = self.create_token(time_range=start_date)
        assert token.is_valid_now is False

        # Not valid anymore
        end_date = DateTimeTZRange(upper=now - timezone.timedelta(days=5))
        token = self.create_token(time_range=end_date)
        assert token.is_valid_now is False

        # Is valid
        time_range = DateTimeTZRange(
            lower=now - timezone.timedelta(days=5),
            upper=now + timezone.timedelta(days=5))
        token = self.create_token(time_range=time_range)
        assert token.is_valid_now

