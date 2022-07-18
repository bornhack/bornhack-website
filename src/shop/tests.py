from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from .factories import OrderFactory
from .factories import OrderProductRelationFactory
from .factories import ProductFactory
from .models import RefundEnum
from economy.factories import PosFactory
from shop.forms import OrderProductRelationForm
from tickets.factories import TicketTypeFactory
from tickets.models import ShopTicket
from utils.factories import UserFactory


class ProductAvailabilityTest(TestCase):
    """Test logic about availability of products."""

    def test_product_available_by_stock(self):
        """If no orders have been made, the product is still available."""
        product = ProductFactory(stock_amount=10)
        self.assertEqual(product.left_in_stock, 10)
        self.assertTrue(product.is_available())

    def test_product_not_available_by_stock(self):
        """If max orders have been made, the product is NOT available."""
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
        """The product is available if now is in the right timeframe."""
        product = ProductFactory()
        # The factory defines the timeframe as now and 31 days forward.
        self.assertTrue(product.is_time_available)
        self.assertTrue(product.is_available())

    def test_product_not_available_by_time(self):
        """The product is not available if now is outside the timeframe."""
        available_in = DateTimeTZRange(
            lower=timezone.now() - timezone.timedelta(5),
            upper=timezone.now() - timezone.timedelta(1),
        )
        product = ProductFactory(available_in=available_in)
        # The factory defines the timeframe as now and 31 days forward.
        self.assertFalse(product.is_time_available)
        self.assertFalse(product.is_available())

    def test_product_is_not_available_yet(self):
        """The product is not available because we are before lower bound."""
        available_in = DateTimeTZRange(lower=timezone.now() + timezone.timedelta(5))
        product = ProductFactory(available_in=available_in)
        # Make sure there is no upper - just in case.
        self.assertEqual(product.available_in.upper, None)
        # The factory defines the timeframe as now and 31 days forward.
        self.assertFalse(product.is_time_available)
        self.assertFalse(product.is_available())

    def test_product_is_available_from_now_on(self):
        """The product is available because we are after lower bound."""
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

        self.assertRedirects(response, reverse("shop:index"))

    def test_product_is_in_order(self):
        # Put the product in an order owned by the user
        OrderProductRelationFactory(
            product=self.product,
            quantity=1,
            order__open=True,
            order__user=self.user,
        )

        self.client.force_login(self.user)
        response = self.client.get(self.path)

        self.assertContains(response, "Update order")

    def test_product_is_in_order_update(self):
        self.product.stock_amount = 2
        self.product.save()

        # Put the product in an order owned by the user
        opr = OrderProductRelationFactory(
            product=self.product,
            quantity=1,
            order__open=True,
            order__user=self.user,
        )

        self.client.force_login(self.user)

        response = self.client.post(self.path, data={"quantity": 2})

        self.assertRedirects(response, reverse("shop:index"))
        opr.refresh_from_db()
        self.assertEqual(opr.quantity, 2)

    def test_product_category_not_public(self):
        self.product.category.public = False
        self.product.category.save()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 404)


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
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("shop:index"))

    def test_redirects_when_cancelled(self):
        self.client.force_login(self.user)

        OrderProductRelationFactory(order=self.order)

        self.order.cancelled = True
        self.order.save()

        response = self.client.get(self.path)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("shop:index"))

    def test_remove_product(self):
        self.client.force_login(self.user)

        OrderProductRelationFactory(order=self.order)
        opr = OrderProductRelationFactory(order=self.order)

        order = opr.order

        data = self.base_form_data
        data["remove_product"] = opr.pk

        response = self.client.post(self.path, data=data)
        self.assertEqual(response.status_code, 200)

        order.refresh_from_db()

        self.assertEqual(order.products.count(), 1)

    def test_remove_last_product_cancels_order(self):
        self.client.force_login(self.user)

        opr = OrderProductRelationFactory(order=self.order)

        order = opr.order

        data = self.base_form_data
        data["remove_product"] = opr.pk

        response = self.client.post(self.path, data=data)
        self.assertEqual(response.status_code, 302)
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
        self.assertEqual(response.status_code, 302)
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(opr.quantity, 11)

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
        self.assertEqual(response.status_code, 200)
        self.assertIn("quantity", response.context["order_product_formset"].errors[0])

    def test_review_and_pay_saves_and_redirects(self):
        self.client.force_login(self.user)

        opr = OrderProductRelationFactory(order=self.order)

        data = self.base_form_data
        data["review_and_pay"] = ""
        data["form-0-id"] = opr.pk
        data["form-0-quantity"] = 5
        data["customer_comment"] = "A comment"
        data["invoice_address"] = "An invoice address"

        response = self.client.post(self.path, data=data)
        self.assertRedirects(
            response,
            reverse("shop:order_review_and_pay", kwargs={"pk": self.order.pk}),
        )

        # Get the updated objects
        opr.refresh_from_db()
        self.order.refresh_from_db()

        # Check them
        self.assertEqual(opr.quantity, 5)
        self.assertEqual(self.order.invoice_address, "An invoice address")
        self.assertEqual(self.order.customer_comment, "A comment")


class TestOrderReviewAndPay(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.order = OrderFactory(user=self.user)
        # Add order
        OrderProductRelationFactory(order=self.order)
        self.path = reverse("shop:order_review_and_pay", kwargs={"pk": self.order.pk})

    def test_terms_have_to_be_accepted(self):
        self.client.force_login(self.user)

        data = {"payment_method": "bank_transfer"}

        response = self.client.post(self.path, data=data)
        self.assertEqual(response.status_code, 200)

    def test_accepted_terms_and_chosen_payment_method(self):
        self.client.force_login(self.user)

        data = {"payment_method": "bank_transfer", "accept_terms": True}

        response = self.client.post(self.path, data=data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("shop:bank_transfer", kwargs={"pk": self.order.id}),
        )


class TestOrderListView(TestCase):
    def test_order_list_view_as_logged_in(self):
        user = UserFactory()
        self.client.force_login(user)
        path = reverse("shop:order_list")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)


class TestTicketCreation(TestCase):
    def test_multiple_tickets_created(self):
        user = UserFactory()
        ticket_type = TicketTypeFactory(single_ticket_per_product=False)
        product = ProductFactory(ticket_type=ticket_type)
        order = OrderFactory(user=user)
        OrderProductRelationFactory(order=order, product=product, quantity=5)
        order.mark_as_paid()
        self.assertEqual(
            ShopTicket.objects.filter(product=product, opr__order=order).count(),
            5,
        )

    def test_single_ticket_created(self):
        user = UserFactory()
        ticket_type = TicketTypeFactory(single_ticket_per_product=True)
        product = ProductFactory(ticket_type=ticket_type)
        order = OrderFactory(user=user)
        OrderProductRelationFactory(order=order, product=product, quantity=5)
        order.mark_as_paid()
        self.assertEqual(
            ShopTicket.objects.filter(product=product, opr__order=order).count(),
            1,
        )


class TestOrderProductRelationModel(TestCase):
    def test_refunded_cannot_be_larger_than_quantity(self):
        """OrderProductRelation with refunded > quantity should raise an IntegrityError."""
        user = UserFactory()
        info_user = UserFactory(username="info")
        ticket_type = TicketTypeFactory(single_ticket_per_product=False)
        product = ProductFactory(ticket_type=ticket_type)
        order = OrderFactory(user=user)
        opr = OrderProductRelationFactory(order=order, product=product, quantity=5)
        refund = order.create_refund(created_by=info_user)
        with self.assertRaises(ValidationError):
            opr.create_rpr(refund=refund, quantity=6)

    def test_refunded_possible(self):
        user = UserFactory()
        info_user = UserFactory(username="info")
        ticket_type = TicketTypeFactory(single_ticket_per_product=False)
        product = ProductFactory(ticket_type=ticket_type)
        order = OrderFactory(user=user)
        opr = OrderProductRelationFactory(order=order, product=product, quantity=5)
        opr.create_tickets()

        # Quantity is 5, we should be able to refund 5
        self.assertEqual(opr.possible_refund, 5)

        # Mark a ticket as used
        ticket1 = opr.shoptickets.first()
        ticket1.mark_as_used(pos=PosFactory(), user=UserFactory())

        # Quantity is 5, but 1 is used, so we should be able to refund 4
        self.assertEqual(opr.possible_refund, 4)

        refund = order.create_refund(created_by=info_user)

        # Refund 1 ticket
        opr.create_rpr(refund=refund, quantity=1)
        opr.save()

        # Quantity is 4, but 1 is used and 1 is refunded, so we should be able to refund 4
        self.assertEqual(opr.possible_refund, 3)


class TestRefund(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.info_user = UserFactory(username="info")
        self.order = OrderFactory(user=self.user)
        self.opr1 = OrderProductRelationFactory(order=self.order, quantity=5)
        self.opr2 = OrderProductRelationFactory(order=self.order, quantity=1)
        self.opr3 = OrderProductRelationFactory(order=self.order, quantity=10)
        self.order.mark_as_paid()

    def test_order_refunded(self):
        self.assertTrue(self.order.refunded == RefundEnum.NOT_REFUNDED.value)

        refund1 = self.order.create_refund(created_by=self.info_user)
        self.opr1.create_rpr(refund=refund1, quantity=1)

        self.assertTrue(self.order.refunded == RefundEnum.PARTIALLY_REFUNDED.value)

        refund2 = self.order.create_refund(created_by=self.info_user)
        self.opr1.create_rpr(refund=refund2, quantity=4)
        self.opr2.create_rpr(refund=refund2, quantity=1)
        self.opr3.create_rpr(refund=refund2, quantity=10)

        self.assertTrue(self.order.refunded == RefundEnum.FULLY_REFUNDED.value)
