from __future__ import annotations

from django.core.exceptions import ValidationError

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

    def create_token(self, token_str: str) -> Token:
        """Helper method for creating tokens"""
        return Token.objects.create(
            token=token_str,
            camp=self.camp,
            category=self.category,
            hint="Test token hint",
            description="Test token description",
            active=True,
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
