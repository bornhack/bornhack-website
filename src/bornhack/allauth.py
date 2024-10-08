"""Custom allauth account adapter based on allauth_2fa.adapter.OTPAdapter."""

from allauth_2fa.adapter import OTPAdapter
import uuid


class UsernameUUIDAdapter(OTPAdapter):
    """Custom allauth account adapter based on allauth_2fa.adapter.OTPAdapter."""

    def generate_unique_username(txts, regex=None):
        """Generate a UUID4 as username."""
        return str(uuid.uuid4())
