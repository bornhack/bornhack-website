"""Custom allauth account adapter based on allauth.account.adapter.DefaultAccountAdapter."""

from __future__ import annotations

import uuid

from allauth.account.adapter import DefaultAccountAdapter


class UsernameUUIDAdapter(DefaultAccountAdapter):
    """Custom allauth account adapter based on allauth.account.adapter.DefaultAccountAdapter."""

    def generate_unique_username(txts, regex=None):
        """Generate a UUID4 as username."""
        return str(uuid.uuid4())
