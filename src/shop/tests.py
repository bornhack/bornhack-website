from django.test import TestCase

from .factories import (
    ProductFactory,
    OrderFactory,
    OrderProductRelationFactory,
)


class ProductAvailabilityTest(TestCase):
    """ Test logic about availability of products. """

    def test_product_available_by_stock(self):
        """ If no orders have been made, the product is still available. """
        product = ProductFactory(stock_amount=10)
        self.assertEqual(product.left_in_stock(), 10)
        self.assertTrue(product.is_available)

    def test_product_not_available_by_stock(self):
        """ If max orders have been made, the product is NOT available. """
        product = ProductFactory(stock_amount=2)

        for i in range(2):
            opr = OrderProductRelationFactory(product=product)
            order = opr.order
            order.paid = True
            order.save()

        self.assertEqual(product.left_in_stock(), 0)
        self.assertFalse(product.is_available())
