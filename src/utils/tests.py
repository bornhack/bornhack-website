from __future__ import annotations

from unittest import skip

from django.core.management import call_command
from django.test import TestCase


class TestBootstrapScript(TestCase):
    """Test bootstrap_devsite script (touching many codepaths)"""

    @skip
    def test_bootstrap_script(self):
        """If no orders have been made, the product is still available."""
        call_command("bootstrap_devsite")
