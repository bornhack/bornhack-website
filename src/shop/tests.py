from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from shop.forms import OrderProductRelationForm
from utils.factories import UserFactory
from .factories import ProductFactory, OrderProductRelationFactory, OrderFactory


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

        form = OrderProductRelationForm({"quantity": 1}, instance=opr)
        self.assertTrue(form.is_valid())

    def test_clean_quantity_fails_when_stock_exceeded(self):
        product = ProductFactory(stock_amount=2)
        # Mark an order as paid/reserved by setting open to None
        OrderProductRelationFactory(product=product, quantity=1, order__open=None)

        # There should only be 1 product left, since we just reserved 1
        opr2 = OrderProductRelationFactory(product=product)

        form = OrderProductRelationForm({"quantity": 2}, instance=opr2)
        self.assertFalse(form.is_valid())

    def test_clean_quantity_when_no_stock_amount(self):
        product = ProductFactory()
        opr = OrderProductRelationFactory(product=product)
        form = OrderProductRelationForm({"quantity": 3}, instance=opr)
        self.assertTrue(form.is_valid())


class TestProductDetailView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.product = ProductFactory()
        self.path = reverse("shop:product_detail", kwargs={"slug": self.product.slug})

    def test_product_is_available_for_anonymous_user(self):
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, 200)

    def test_product_is_available_for_logged_in_user(self):
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

        response = self.client.post(self.path, data={"quantity": 1})

        order = self.user.orders.get()

        self.assertRedirects(
            response, reverse("shop:order_detail", kwargs={"pk": order.pk})
        )

    def test_product_is_in_order(self):
        # Put the product in an order owned by the user
        OrderProductRelationFactory(
            product=self.product, quantity=1, order__open=True, order__user=self.user
        )

        self.client.force_login(self.user)
        response = self.client.get(self.path)

        self.assertContains(response, "Update order")

    def test_product_is_in_order_update(self):
        self.product.stock_amount = 2
        self.product.save()

        # Put the product in an order owned by the user
        opr = OrderProductRelationFactory(
            product=self.product, quantity=1, order__open=True, order__user=self.user
        )

        self.client.force_login(self.user)

        response = self.client.post(self.path, data={"quantity": 2})

        self.assertRedirects(
            response, reverse("shop:order_detail", kwargs={"pk": opr.order.pk})
        )
        opr.refresh_from_db()
        self.assertEquals(opr.quantity, 2)

    def test_product_category_not_public(self):
        self.product.category.public = False
        self.product.category.save()
        response = self.client.get(self.path)
        self.assertEquals(response.status_code, 404)


class TestOrderDetailView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.order = OrderFactory(user=self.user)
        self.path = reverse("shop:order_detail", kwargs={"pk": self.order.pk})

        # We are using a formset which means we have to include some "management form" data.
        self.base_form_data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "",
        }

    def test_redirects_when_no_products(self):
        self.client.force_login(self.user)
        response = self.client.get(self.path)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("shop:index"))

    def test_redirects_when_cancelled(self):
        self.client.force_login(self.user)

        OrderProductRelationFactory(order=self.order)

        self.order.cancelled = True
        self.order.save()

        response = self.client.get(self.path)

        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("shop:index"))

    def test_remove_product(self):
        self.client.force_login(self.user)

        OrderProductRelationFactory(order=self.order)
        opr = OrderProductRelationFactory(order=self.order)

        order = opr.order

        data = self.base_form_data
        data["remove_product"] = opr.pk

        response = self.client.post(self.path, data=data)
        self.assertEquals(response.status_code, 200)

        order.refresh_from_db()

        self.assertEquals(order.products.count(), 1)

    def test_remove_last_product_cancels_order(self):
        self.client.force_login(self.user)

        opr = OrderProductRelationFactory(order=self.order)

        order = opr.order

        data = self.base_form_data
        data["remove_product"] = opr.pk

        response = self.client.post(self.path, data=data)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("shop:index"))

        order.refresh_from_db()

        self.assertTrue(order.cancelled)

    def test_cancel_order(self):
        self.client.force_login(self.user)

        opr = OrderProductRelationFactory(order=self.order)
        order = opr.order

        data = self.base_form_data
        data["cancel_order"] = ""

        response = self.client.post(self.path, data=data)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(response, reverse("shop:index"))

        order.refresh_from_db()

        self.assertTrue(order.cancelled)

    def test_incrementing_product_quantity(self):
        self.client.force_login(self.user)

        opr = OrderProductRelationFactory(order=self.order)
        opr.product.stock_amount = 100
        opr.product.save()

        data = self.base_form_data
        data["update_order"] = ""
        data["form-0-id"] = opr.pk
        data["form-0-quantity"] = 11

        response = self.client.post(self.path, data=data)
        opr.refresh_from_db()
        self.assertEquals(response.status_code, 200)
        self.assertEquals(opr.quantity, 11)

    def test_incrementing_product_quantity_beyond_stock_fails(self):
        self.client.force_login(self.user)

        opr = OrderProductRelationFactory(order=self.order)
        opr.product.stock_amount = 10
        opr.product.save()

        data = self.base_form_data
        data["update_order"] = ""
        data["form-0-id"] = opr.pk
        data["form-0-quantity"] = 11

        response = self.client.post(self.path, data=data)
        self.assertEquals(response.status_code, 200)
        self.assertIn("quantity", response.context["order_product_formset"].errors[0])

    def test_terms_have_to_be_accepted(self):
        self.client.force_login(self.user)

        opr = OrderProductRelationFactory(order=self.order)

        data = self.base_form_data
        data["form-0-id"] = opr.pk
        data["form-0-quantity"] = 11
        data["payment_method"] = "bank_transfer"

        response = self.client.post(self.path, data=data)
        self.assertEquals(response.status_code, 200)

    def test_accepted_terms_and_chosen_payment_method(self):
        self.client.force_login(self.user)

        opr = OrderProductRelationFactory(order=self.order)

        data = self.base_form_data
        data["form-0-id"] = opr.pk
        data["form-0-quantity"] = 11
        data["payment_method"] = "bank_transfer"
        data["accept_terms"] = True

        response = self.client.post(self.path, data=data)
        self.assertEquals(response.status_code, 302)
        self.assertRedirects(
            response, reverse("shop:bank_transfer", kwargs={"pk": self.order.id})
        )


class TestOrderListView(TestCase):
    def test_order_list_view_as_logged_in(self):
        user = UserFactory()
        self.client.force_login(user)
        path = reverse("shop:order_list")
        response = self.client.get(path)
        self.assertEquals(response.status_code, 200)
