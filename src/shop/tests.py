from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from psycopg2.extras import DateTimeTZRange

from camps.factories import CampFactory
from camps.models import Camp
from camps.models import Permission as CampPermission
from economy.factories import PosFactory
from shop.forms import OrderProductRelationForm
from teams.models import Team
from teams.models import TeamMember
from tickets.factories import TicketTypeFactory
from tickets.models import ShopTicket
from tickets.models import TicketGroup
from utils.factories import UserFactory

from .factories import OrderFactory
from .factories import OrderProductRelationFactory
from .factories import ProductFactory
from .factories import SubProductRelationFactory
from .models import Order
from .models import OrderProductRelation
from .models import Product
from .models import RefundEnum


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
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_multiple_tickets_created(self):
        ticket_type = TicketTypeFactory(single_ticket_per_product=False)
        product = ProductFactory(ticket_type=ticket_type)
        order = OrderFactory(user=self.user)
        OrderProductRelationFactory(order=order, product=product, quantity=5)
        order.mark_as_paid()
        self.assertEqual(
            ShopTicket.objects.filter(product=product, opr__order=order).count(),
            5,
        )

    def test_single_ticket_created(self):
        ticket_type = TicketTypeFactory(single_ticket_per_product=True)
        product = ProductFactory(ticket_type=ticket_type)
        order = OrderFactory(user=self.user)
        OrderProductRelationFactory(order=order, product=product, quantity=5)
        order.mark_as_paid()
        self.assertEqual(
            ShopTicket.objects.filter(product=product, opr__order=order).count(),
            1,
        )

    def test_sub_products_created_sub_product_single_ticket_per_product_false(self):
        bundle_product = ProductFactory()
        sub_product = ProductFactory(
            ticket_type=TicketTypeFactory(single_ticket_per_product=False),
        )
        bundle_product.sub_products.add(
            sub_product,
            through_defaults={"number_of_tickets": 5},
        )
        order = OrderFactory(user=self.user)
        OrderProductRelationFactory(order=order, product=bundle_product, quantity=1)
        order.mark_as_paid()
        self.assertEqual(
            ShopTicket.objects.filter(product=sub_product, opr__order=order).count(),
            5,
        )

    def test_sub_products_created_sub_product_single_ticket_per_product_true(self):
        bundle_product = ProductFactory()
        sub_product = ProductFactory(
            ticket_type=TicketTypeFactory(single_ticket_per_product=True),
        )
        bundle_product.sub_products.add(
            sub_product,
            through_defaults={"number_of_tickets": 5},
        )
        order = OrderFactory(user=self.user)
        OrderProductRelationFactory(order=order, product=bundle_product, quantity=1)
        order.mark_as_paid()
        self.assertEqual(
            ShopTicket.objects.filter(product=sub_product, opr__order=order).count(),
            1,
        )

    def test_ticket_generation_is_idempotent(self):
        """Test that calling create_tickets multiple times does not create more tickets."""
        bundle_product = ProductFactory()
        sub_product = ProductFactory(
            ticket_type=TicketTypeFactory(),
        )
        bundle_product.sub_products.add(
            sub_product,
            through_defaults={"number_of_tickets": 5},
        )
        order = OrderFactory(user=self.user)
        OrderProductRelationFactory(order=order, product=bundle_product, quantity=2)

        order.mark_as_paid()
        self.assertEqual(
            ShopTicket.objects.filter(opr__order=order).count(),
            10,
        )
        self.assertEqual(
            TicketGroup.objects.filter(opr=order.oprs.first()).count(),
            2,
        )

        # Calling create_tickets again should not create more tickets
        order.create_tickets()
        self.assertEqual(
            ShopTicket.objects.filter(opr__order=order).count(),
            10,
        )
        self.assertEqual(
            TicketGroup.objects.filter(opr=order.oprs.first()).count(),
            2,
        )

        # Add a new sub product to the bundle
        sub_product_2 = ProductFactory(
            ticket_type=TicketTypeFactory(),
        )
        bundle_product.sub_products.add(
            sub_product_2,
            through_defaults={"number_of_tickets": 5},
        )

        # Calling create_tickets again should create 10 new tickets
        order.create_tickets()
        self.assertEqual(
            ShopTicket.objects.filter(opr__order=order).count(),
            20,
        )
        self.assertEqual(
            TicketGroup.objects.filter(opr=order.oprs.first()).count(),
            2,
        )

        # Calling create_tickets again should not create more tickets
        order.create_tickets()
        self.assertEqual(
            ShopTicket.objects.filter(opr__order=order).count(),
            20,
        )
        self.assertEqual(
            TicketGroup.objects.filter(opr=order.oprs.first()).count(),
            2,
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
    camp: Camp
    user: User
    info_user: User
    order: Order
    bundle_product: Product
    sub_product: Product
    opr1: OrderProductRelation
    opr2: OrderProductRelation
    opr3: OrderProductRelation
    opr4: OrderProductRelation

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.info_user = UserFactory(username="info")

        cls.camp = CampFactory()
        infoteam = Team.objects.create(
            name="Info",
            description="Info team",
            camp=cls.camp,
        )
        permission_content_type = ContentType.objects.get_for_model(CampPermission)
        permission = Permission.objects.get(
            content_type=permission_content_type,
            codename="info_team_member",
        )
        infoteam.group.permissions.add(permission)
        TeamMember.objects.create(user=cls.info_user, team=infoteam, approved=True)
        cls.bundle_product = ProductFactory()
        cls.sub_product = ProductFactory(ticket_type=TicketTypeFactory())
        SubProductRelationFactory(
            bundle_product=cls.bundle_product,
            sub_product=cls.sub_product,
            number_of_tickets=3,
        )

        cls.order = OrderFactory(user=cls.user)
        cls.opr1 = OrderProductRelationFactory(
            order=cls.order,
            quantity=5,
            product__ticket_type=TicketTypeFactory(),
        )
        cls.opr2 = OrderProductRelationFactory(
            order=cls.order,
            quantity=1,
            product__ticket_type=TicketTypeFactory(),
        )
        cls.opr3 = OrderProductRelationFactory(
            order=cls.order,
            quantity=10,
            product__ticket_type=TicketTypeFactory(),
        )
        cls.opr4 = OrderProductRelationFactory(
            order=cls.order,
            product=cls.bundle_product,
            quantity=2,
        )
        cls.order.mark_as_paid()

    def test_order_refunded(self):
        self.assertTrue(self.order.refunded == RefundEnum.NOT_REFUNDED.value)

        refund1 = self.order.create_refund(created_by=self.info_user)
        self.opr1.create_rpr(refund=refund1, quantity=1)

        self.assertTrue(self.order.refunded == RefundEnum.PARTIALLY_REFUNDED.value)

        refund2 = self.order.create_refund(created_by=self.info_user)
        self.opr1.create_rpr(refund=refund2, quantity=4)
        self.opr2.create_rpr(refund=refund2, quantity=1)
        self.opr3.create_rpr(refund=refund2, quantity=10)
        self.opr4.create_rpr(refund=refund2, quantity=2)

        self.assertTrue(self.order.refunded == RefundEnum.FULLY_REFUNDED.value)

    def test_refund_backoffice_view(self):
        url = reverse(
            "backoffice:order_refund",
            kwargs={"camp_slug": self.camp.slug, "order_id": self.order.id},
        )
        self.client.force_login(self.info_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # We show both bundles and tickets
        self.assertInHTML("<h4>Bundles</h4>", response.rendered_content)
        self.assertInHTML("<h4>Tickets</h4>", response.rendered_content)

        # We show the correct number of tickets
        for opr in [self.opr1, self.opr2, self.opr3]:
            self.assertInHTML(
                f"<td>{opr.product}</td><td>{opr.quantity}</td>",
                response.rendered_content,
            )

        # OPR 4 is a bundle, so we test that separately
        self.assertInHTML(
            f"<td>{self.bundle_product}<br><small>3 x {self.sub_product.name}</small></td>",
            response.rendered_content,
            count=2,
        )

        # Now to refunding
        self.assertEqual(self.opr1.non_refunded_quantity, 5)
        form_data = self._get_form_data(
            refund_tickets=[self.opr1.shoptickets.order_by("created").first()],
        )
        response = self.client.post(url, form_data)

        self.assertEqual(response.status_code, 302)
        self.opr1.refresh_from_db()
        self.assertEqual(self.opr1.refunded_quantity, 1)
        self.assertEqual(self.opr1.non_refunded_quantity, 4)

        # Now to refunding a bundle
        form_data = self._get_form_data(
            refund_ticket_groups=[self.opr4.ticketgroups.order_by("created").first()],
        )
        response = self.client.post(url, form_data)

        self.assertEqual(response.status_code, 302)
        self.opr4.refresh_from_db()
        self.assertEqual(self.opr4.refunded_quantity, 1)
        self.assertEqual(self.opr4.non_refunded_quantity, 1)

    def _get_form_data(
        self,
        *,
        refund_tickets: list[ShopTicket] | None = None,
        refund_ticket_groups: list[TicketGroup] | None = None,
    ):
        """Helper method to get the form data for a refund"""
        refund_tickets = refund_tickets or []
        refund_ticket_groups = refund_ticket_groups or []
        form_data = {}

        for opr in [self.opr1, self.opr2, self.opr3]:
            form_data[f"ticket-{opr.id}-TOTAL_FORMS"] = "1"
            form_data[f"ticket-{opr.id}-INITIAL_FORMS"] = "1"
            form_data[f"ticket-{opr.id}-MIN_NUM_FORMS"] = "0"
            form_data[f"ticket-{opr.id}-MAX_NUM_FORMS"] = "1000"
            for index, ticket in enumerate(opr.shoptickets.all()):
                form_data[f"ticket-{opr.id}-{index}-uuid"] = str(ticket.uuid)
                if ticket in refund_tickets:
                    print(
                        f"Refunding ticket {ticket}, index {index}, uuid {ticket.uuid}",
                    )
                    form_data[f"ticket-{opr.id}-{index}-refund"] = "on"

        for opr in [self.opr4]:
            form_data[f"ticket-group-{opr.id}-TOTAL_FORMS"] = "1"
            form_data[f"ticket-group-{opr.id}-INITIAL_FORMS"] = "1"
            form_data[f"ticket-group-{opr.id}-MIN_NUM_FORMS"] = "0"
            form_data[f"ticket-group-{opr.id}-MAX_NUM_FORMS"] = "1000"
            for index, ticket_group in enumerate(opr.ticketgroups.all()):
                form_data[f"ticket-group-{opr.id}-{index}-uuid"] = str(
                    ticket_group.uuid,
                )
                if ticket_group in refund_ticket_groups:
                    form_data[f"ticket-group-{opr.id}-{index}-refund"] = "on"

        return form_data
