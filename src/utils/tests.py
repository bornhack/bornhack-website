from django.core.management import call_command
from django.test import TestCase


class ProductAvailabilityTest(TestCase):
    """ Test bootstrap_devsite script (touching many codepaths) """

    def test_bootstrap_script(self):
        """ If no orders have been made, the product is still available. """
        call_command("bootstrap_devsite")
