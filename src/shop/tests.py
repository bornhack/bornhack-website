from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from psycopg2.extras import DateTimeTZRange

from shop.forms import OrderProductRelationForm
from utils.factories import UserFactory
from .factories import ProductFactory, OrderProductRelationFactory


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
        opr1.order.mark_as_paid()
        opr2 = OrderProductRelationFactory(product=product)
        opr2.order.mark_as_paid()

        self.assertEqual(product.left_in_stock, 0)
        self.assertFalse(product.is_stock_available)
        self.assertFalse(product.is_available())

        # Cancel one order
        opr1.order.cancelled = True
        opr1.order.save()

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
            upper=timezone.now() - timezone.timedelta(1),
        )
        product = ProductFactory(available_in=available_in)
        # The factory defines the timeframe as now and 31 days forward.
        self.assertFalse(product.is_time_available)
        self.assertFalse(product.is_available())

    def test_product_is_not_available_yet(self):
        """ The product is not available because we are before lower bound. """
        available_in = DateTimeTZRange(lower=timezone.now() + timezone.timedelta(5))
        product = ProductFactory(available_in=available_in)
        # Make sure there is no upper - just in case.
        self.assertEqual(product.available_in.upper, None)
        # The factory defines the timeframe as now and 31 days forward.
        self.assertFalse(product.is_time_available)
        self.assertFalse(product.is_available())

    def test_product_is_available_from_now_on(self):
        """ The product is available because we are after lower bound. """
        available_in = DateTimeTZRange(lower=timezone.now() - timezone.timedelta(1))
        product = ProductFactory(available_in=available_in)
        # Make sure there is no upper - just in case.
        self.assertEqual(product.available_in.upper, None)
        # The factory defines the timeframe as now and 31 days forward.
        self.assertTrue(product.is_time_available)
        self.assertTrue(product.is_available())


class TestOrderProductRelationForm(TestCase):
    def test_clean_quantity_succeeds_when_stock_not_exceeded(self):
        product = ProductFactory(stock_amount=2)

        # Mark an order as paid/reserved by setting open to None
        opr1 = OrderProductRelationFactory(product=product, quantity=1)
        opr1.order.open = None
        opr1.order.save()

        opr2 = OrderProductRelationFactory(product=product, quantity=1)

        form = OrderProductRelationForm(instance=opr2)
        self.assertTrue(form.is_valid)

    def test_clean_quantity_fails_when_stock_exceeded(self):
        product = ProductFactory(stock_amount=2)
        # Mark an order as paid/reserved by setting open to None
        opr1 = OrderProductRelationFactory(product=product, quantity=1)
        opr1.order.open = None
        opr1.order.save()

        # There should only be 1 product left, since we just reserved 1
        opr2 = OrderProductRelationFactory(product=product, quantity=2)

        form = OrderProductRelationForm(instance=opr2)
        self.assertFalse(form.is_valid())


class TestProductDetailView(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_product_is_available(self):
        product = ProductFactory()
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("shop:product_detail", kwargs={"slug": product.slug})
        )

        self.assertIn("Add to order", str(response.content))
        self.assertEqual(response.status_code, 200)

    def test_product_is_available_with_stock_left(self):
        product = ProductFactory(stock_amount=2)

        opr1 = OrderProductRelationFactory(product=product, quantity=1)
        opr1.order.open = None
        opr1.order.save()

        self.client.force_login(self.user)
        response = self.client.get(
            reverse("shop:product_detail", kwargs={"slug": product.slug})
        )

        self.assertIn("<bold>1</bold> available", str(response.content))
        self.assertEqual(response.status_code, 200)

    def test_product_is_sold_out(self):
        product = ProductFactory(stock_amount=1)

        opr1 = OrderProductRelationFactory(product=product, quantity=1)
        opr1.order.open = None
        opr1.order.save()

        self.client.force_login(self.user)
        response = self.client.get(
            reverse("shop:product_detail", kwargs={"slug": product.slug})
        )

        self.assertIn("Sold out.", str(response.content))
        self.assertEqual(response.status_code, 200)
