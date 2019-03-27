from django.test import TestCase
from django.utils import timezone

from psycopg2.extras import DateTimeTZRange

from .factories import (
    ProductFactory,
    OrderProductRelationFactory,
)


class ProductAvailabilityTest(TestCase):
    """ Test logic about availability of products. """

    def test_product_available_by_stock(self):
        """ If no orders have been made, the product is still available. """
        product = ProductFactory(stock_amount=10)
        self.assertEqual(product.left_in_stock, 10)
        self.assertTrue(product.is_available())

    def test_product_not_available_by_stock(self):
        """ If max orders have been made, the product is NOT available. """
        product = ProductFactory(stock_amount=2)

        opr1 = OrderProductRelationFactory(product=product)
        opr2 = OrderProductRelationFactory(product=product)

        self.assertEqual(product.left_in_stock, 0)
        self.assertFalse(product.is_stock_available)
        self.assertFalse(product.is_available())

        # Cancel one order
        opr1.order.mark_as_cancelled()

        self.assertEqual(product.left_in_stock, 1)
        self.assertTrue(product.is_stock_available)
        self.assertTrue(product.is_available())


    def test_product_available_by_time(self):
        """ The product is available if now is in the right timeframe. """
        product = ProductFactory()
        # The factory defines the timeframe as now and 31 days forward.
        self.assertTrue(product.is_time_available)
        self.assertTrue(product.is_available())

    def test_product_not_available_by_time(self):
        """ The product is not available if now is outside the timeframe. """
        available_in = DateTimeTZRange(
            lower=timezone.now() - timezone.timedelta(5),
            upper=timezone.now() - timezone.timedelta(1)
        )
        product = ProductFactory(available_in=available_in)
        # The factory defines the timeframe as now and 31 days forward.
        self.assertFalse(product.is_time_available)
        self.assertFalse(product.is_available())

    def test_product_is_not_available_yet(self):
        """ The product is not available because we are before lower bound. """
        available_in = DateTimeTZRange(
            lower=timezone.now() + timezone.timedelta(5)
        )
        product = ProductFactory(available_in=available_in)
        # Make sure there is no upper - just in case.
        self.assertEqual(product.available_in.upper, None)
        # The factory defines the timeframe as now and 31 days forward.
        self.assertFalse(product.is_time_available)
        self.assertFalse(product.is_available())

    def test_product_is_available_from_now_on(self):
        """ The product is available because we are after lower bound. """
        available_in = DateTimeTZRange(
            lower=timezone.now() - timezone.timedelta(1)
        )
        product = ProductFactory(available_in=available_in)
        # Make sure there is no upper - just in case.
        self.assertEqual(product.available_in.upper, None)
        # The factory defines the timeframe as now and 31 days forward.
        self.assertTrue(product.is_time_available)
        self.assertTrue(product.is_available())
