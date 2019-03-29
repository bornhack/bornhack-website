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

        OrderProductRelationFactory(product=product, order__open=None)
        opr = OrderProductRelationFactory(product=product, order__open=None)

        self.assertEqual(product.left_in_stock, 0)
        self.assertFalse(product.is_stock_available)
        self.assertFalse(product.is_available())

        # Cancel one order
        opr.order.cancelled = True
        opr.order.save()

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
        OrderProductRelationFactory(product=product, quantity=1, order__open=None)

        opr = OrderProductRelationFactory(product=product)

        form = OrderProductRelationForm({'quantity': 1}, instance=opr)
        self.assertTrue(form.is_valid())

    def test_clean_quantity_fails_when_stock_exceeded(self):
        product = ProductFactory(stock_amount=2)
        # Mark an order as paid/reserved by setting open to None
        OrderProductRelationFactory(product=product, quantity=1, order__open=None)

        # There should only be 1 product left, since we just reserved 1
        opr2 = OrderProductRelationFactory(product=product)

        form = OrderProductRelationForm({'quantity': 2}, instance=opr2)
        self.assertFalse(form.is_valid())

    def test_clean_quantity_when_no_stock_amount(self):
        product = ProductFactory()
        opr = OrderProductRelationFactory(product=product)
        form = OrderProductRelationForm({'quantity': 3}, instance=opr)
        self.assertTrue(form.is_valid())


class TestProductDetailView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.product = ProductFactory()
        self.path = reverse("shop:product_detail", kwargs={"slug": self.product.slug})

    def test_product_is_available(self):
        self.client.force_login(self.user)
        response = self.client.get(self.path)

        self.assertContains(response, "Add to order")
        self.assertEqual(response.status_code, 200)

    def test_product_is_available_with_stock_left(self):
        self.product.stock_amount = 2
        self.product.save()

        OrderProductRelationFactory(product=self.product, quantity=1, order__open=None)

        self.client.force_login(self.user)
        response = self.client.get(self.path)

        self.assertContains(response, "<bold>1</bold> available")
        self.assertEqual(response.status_code, 200)

    def test_product_is_sold_out(self):
        self.product.stock_amount = 1
        self.product.save()

        OrderProductRelationFactory(product=self.product, quantity=1, order__open=None)

        self.client.force_login(self.user)
        response = self.client.get(self.path)

        self.assertContains(response, "Sold out.")
        self.assertEqual(response.status_code, 200)

    def test_adding_product_to_new_order(self):
        self.client.force_login(self.user)

        response = self.client.post(self.path, data={'quantity': 1})

        order = self.user.orders.get()

        self.assertRedirects(response, reverse('shop:order_detail', kwargs={"pk": order.pk}))

    def test_product_is_in_order(self):
        # Put the product in an order owned by the user
        OrderProductRelationFactory(product=self.product, quantity=1, order__open=True, order__user=self.user)

        self.client.force_login(self.user)
        response = self.client.get(self.path)

        self.assertContains(response, "Update order")

    def test_product_is_in_order_update(self):
        self.product.stock_amount = 2
        self.product.save()

        # Put the product in an order owned by the user
        opr = OrderProductRelationFactory(product=self.product, quantity=1, order__open=True, order__user=self.user)

        self.client.force_login(self.user)

        response = self.client.post(self.path, data={'quantity': 2})

        self.assertRedirects(response, reverse('shop:order_detail', kwargs={"pk": opr.order.pk}))
        opr.refresh_from_db()
        self.assertEquals(opr.quantity, 2)

    def test_product_category_not_public(self):
        self.product.category.public = False
        self.product.category.save()
        response = self.client.get(self.path)
        self.assertEquals(response.status_code, 404)
