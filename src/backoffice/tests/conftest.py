import pytest
import uuid

from tokens.models import TokenCategory
from tokens.models import TokenFind
from tokens.models import Token


@pytest.fixture
def token_category_factory(db):
    """Fixture for returning a factory function."""

    def create_token_category(persist=False, **kwargs) -> TokenCategory:
        """Create a TokenCategory instance. Saves to DB if persist=True."""
        defaults = {
            "name": "token-category",
            "description": "token category description",
        }

        defaults.update(**kwargs)

        category = TokenCategory(**defaults)

        if persist:
            category.save()

        return category

    return create_token_category


@pytest.fixture
def token_category(token_category_factory) -> TokenCategory:
    """Fixture for a single TokenCategory"""
    return token_category_factory(persist=True)


@pytest.fixture
def token_factory(db, camp, token_category):
    """Fixture for returning a factory function."""

    def create_token(persist=False, **kwargs) -> Token:
        """Create a Token instance. Saves to DB if persist=True."""
        defaults = {
            "category": token_category,
            "camp": camp,
            "token": str(uuid.uuid4()).replace('-', ''),
            "hint": "token-hint",
            "description": "token description",
            "active": True,
            "valid_when": None,
        }

        defaults.update(**kwargs)

        token = Token(**defaults)

        if persist:
            token.save()

        return token

    return create_token


@pytest.fixture
def token(token_factory) -> Token:
    """Fixture for returning a single active token"""
    return token_factory(persist=True)


@pytest.fixture
def token_find_factory(db, token, users):
    """Fixture for returning a factory function."""

    def create_token_find(persist=False, **kwargs) -> TokenFind:
        """Create a TokenFind instance. Saves to DB if persist=True."""
        defaults = {
            "token": token,
            "user": users[0],
        }

        defaults.update(**kwargs)

        token_find = TokenFind(**defaults)

        if persist:
            token_find.save()

        return token_find

    return create_token_find


@pytest.fixture
def token_find(token_find_factory) -> TokenFind:
    """Fixture for returning a single token find."""
    return token_find_factory(persist=True)

