import logging
from datetime import timedelta
from decimal import Decimal
from enum import Enum
from itertools import chain

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.postgres.fields import DateTimeRangeField
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.db.models import Case
from django.db.models import Count
from django.db.models import F
from django.db.models import Sum
from django.db.models import Value
from django.db.models import When
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from unidecode import unidecode

from .managers import OrderQuerySet
from .managers import ProductQuerySet
from utils.models import CreatedUpdatedModel
from utils.models import UUIDModel
from utils.slugs import unique_slugify

logger = logging.getLogger("bornhack.%s" % __name__)


class CustomOrder(ExportModelOperationsMixin("custom_order"), CreatedUpdatedModel):
    text = models.TextField(help_text=_("The invoice text"))

    customer = models.TextField(help_text=_("The customer info for this order"))

    amount = models.IntegerField(
        help_text=_("Amount of this custom order (in DKK, including VAT)."),
    )

    paid = models.BooleanField(
        verbose_name=_("Paid?"),
        help_text=_(
            "Check when this custom order has been paid (or if it gets cancelled out by a Credit Note)",
        ),
        default=False,
    )

    danish_vat = models.BooleanField(help_text="Danish VAT?", default=True)

    def __str__(self):
        return "custom order id #%s" % self.pk

    @property
    def vat(self):
        if self.danish_vat:
            return Decimal(round(self.amount * Decimal(0.2), 2))
        else:
            return 0


class Order(ExportModelOperationsMixin("order"), CreatedUpdatedModel):
    class Meta:
        unique_together = ("user", "open")
        ordering = ["-created"]

    products = models.ManyToManyField(
        "shop.Product",
        through="shop.OrderProductRelation",
    )

    user = models.ForeignKey(
        "auth.User",
        verbose_name=_("User"),
        help_text=_("The user this shop order belongs to."),
        related_name="orders",
        on_delete=models.PROTECT,
    )

    paid = models.BooleanField(
        verbose_name=_("Paid?"),
        help_text=_("Whether this shop order has been paid."),
        default=False,
    )

    # We are using a nullable BooleanField here to ensure that we only have one open order per user at a time.
    # This "hack" is possible since postgres treats null values as different, and thus we have database level integrity.
    open = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_("Open?"),
        help_text=_('Whether this shop order is open or not. "None" means closed.'),
        default=True,
    )

    class PaymentMethods(models.TextChoices):
        CREDIT_CARD = "credit_card", "Credit card"
        BLOCKCHAIN = "blockchain", "Blockchain"
        BANK_TRANSFER = "bank_transfer", "Bank transfer"
        IN_PERSON = "in_person", "In Person"

    payment_method = models.CharField(
        max_length=50,
        choices=PaymentMethods.choices,
        default="",
        blank=True,
    )

    cancelled = models.BooleanField(default=False)

    customer_comment = models.TextField(
        verbose_name=_("Customer comment"),
        help_text=_("If you have any comments about the order please enter them here."),
        default="",
        blank=True,
    )

    invoice_address = models.TextField(
        help_text=_(
            "The invoice address for this order. Leave blank to use the email associated with the logged in user.",
        ),
        blank=True,
    )

    notes = models.TextField(
        help_text="Any internal notes about this order can be entered here. They will not be printed on the invoice or shown to the customer in any way.",
        default="",
        blank=True,
    )

    pdf = models.FileField(null=True, blank=True, upload_to="proforma_invoices/")

    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return "shop order id #%s" % self.pk

    def get_number_of_items(self):
        return self.products.aggregate(sum=Sum("orderproductrelation__quantity"))["sum"]

    @property
    def vat(self):
        return Decimal(self.total * Decimal(0.2))

    @property
    def total(self):
        if self.products.all():
            return Decimal(
                self.products.aggregate(
                    sum=Sum(
                        models.F("orderproductrelation__product__price")
                        * models.F("orderproductrelation__quantity"),
                        output_field=models.IntegerField(),
                    ),
                )["sum"],
            )
        else:
            return False

    def get_coinify_callback_url(self, request):
        """Check settings for an alternative COINIFY_CALLBACK_HOSTNAME otherwise use the one from the request"""
        if (
            hasattr(settings, "COINIFY_CALLBACK_HOSTNAME")
            and settings.COINIFY_CALLBACK_HOSTNAME
        ):
            host = settings.COINIFY_CALLBACK_HOSTNAME
        else:
            host = request.get_host()
        return (
            "https://"
            + host
            + str(reverse_lazy("shop:coinify_callback", kwargs={"pk": self.pk}))
        )

    def get_coinify_thanks_url(self, request):
        return (
            "https://"
            + request.get_host()
            + str(reverse_lazy("shop:coinify_thanks", kwargs={"pk": self.pk}))
        )

    def get_epay_accept_url(self, request):
        return (
            "https://"
            + request.get_host()
            + str(reverse_lazy("shop:epay_thanks", kwargs={"pk": self.pk}))
        )

    def get_cancel_url(self, request):
        return (
            "https://"
            + request.get_host()
            + str(reverse_lazy("shop:order_detail", kwargs={"pk": self.pk}))
        )

    def get_quickpay_accept_url(self, request):
        return (
            "https://"
            + request.get_host()
            + str(reverse_lazy("shop:quickpay_thanks", kwargs={"pk": self.pk}))
        )

    def get_quickpay_callback_url(self, request):
        return (
            "https://"
            + request.get_host()
            + str(reverse_lazy("shop:quickpay_callback", kwargs={"pk": self.pk}))
        )

    @property
    def description(self):
        return "Order #%s" % self.pk

    def get_absolute_url(self):
        return str(reverse_lazy("shop:order_detail", kwargs={"pk": self.pk}))

    def create_tickets(self, request=None):
        """Calls create_tickets() on each OPR and returns a list of all created tickets."""
        tickets = []
        for opr in self.oprs.all():
            tickets += opr.create_tickets(request)
        return tickets

    def get_tickets(self):
        return chain(*[opr.shoptickets.all() for opr in self.oprs.all()])

    def mark_as_paid(self, request=None):
        self.paid = True
        self.open = None
        self.create_tickets(request)
        self.save()

    def mark_as_cancelled(self, request=None):
        if self.paid:
            msg = "Order %s is paid, cannot cancel a paid order!" % self.pk
            if request:
                messages.error(request, msg)
            else:
                print(msg)
        else:
            self.cancelled = True
            self.open = None
            self.save()

    @property
    def coinifyapiinvoice(self):
        if not self.coinify_api_invoices.exists():
            return False

        for tempinvoice in self.coinify_api_invoices.all():
            # we already have a coinifyinvoice for this order, check if it expired
            if not tempinvoice.expired:
                # this invoice is not expired, we are good to go
                return tempinvoice

        # nope
        return False

    @property
    def filename(self):
        return "bornhack_proforma_invoice_order_%s.pdf" % self.pk

    def get_invoice_address(self):
        if self.invoice_address:
            return self.invoice_address
        else:
            return self.user.email

    @property
    def used_status(self):
        used = len(self.get_used_shoptickets())
        unused = len(self.get_unused_shoptickets())
        return f"{used} / {used+unused}"

    def get_used_shoptickets(self):
        tickets = []
        for opr in self.oprs.all():
            tickets += opr.used_shoptickets
        return tickets

    def get_unused_shoptickets(self):
        tickets = []
        for opr in self.oprs.all():
            tickets += opr.unused_shoptickets
        return tickets

    @property
    def refunded(self) -> str:
        aggregate = self.oprs.aggregate(
            # We want to sum the quantity of distinct OPRs
            total_quantity=Sum("quantity", distinct=True),
            # We want all RPRs per OPR, so therefore no distinct (distinct would give us one RPR per OPR)
            total_refunded=Sum("rprs__quantity"),
        )

        total_refunded = aggregate["total_refunded"]
        total_quantity = aggregate["total_quantity"]

        if total_refunded is None:
            return RefundEnum.NOT_REFUNDED.value

        if total_refunded == total_quantity:
            return RefundEnum.FULLY_REFUNDED.value
        elif total_refunded > 0:
            return RefundEnum.PARTIALLY_REFUNDED.value
        else:
            return RefundEnum.NOT_REFUNDED.value

    def create_refund(self, *, created_by: User, notes: str = "") -> "Refund":
        return Refund.objects.create(order=self, notes=notes, created_by=created_by)


# ########## REFUNDS #################################################


class RefundEnum(Enum):
    NOT_REFUNDED = "NOT_REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    FULLY_REFUNDED = "FULLY_REFUNDED"


class Refund(CreatedUpdatedModel):
    """A refund is created whenever we have to refund a webshop Order (partially or fully).

    The Refund model does not have a products m2m like the Order model, instead self.rprs
    returns a QS of the RefundProductRelations for this Refund, which in turn each have an FK
    to the OrderProductRelation they are refunding (partially or fully).

    A Refund is always related to a webshop Order. TODO add a CustomRefund model for when we
    need to create a CreditNote without a related webshop Order.
    """

    class Meta:
        ordering = ["-created"]

    order = models.ForeignKey(
        "shop.Order",
        on_delete=models.PROTECT,
        related_name="refunds",
        help_text="The Order this Refund is refunding (partially or fully)",
    )

    paid = models.BooleanField(
        verbose_name=_("Paid?"),
        help_text=_("Whether this shop refund has been paid."),
        default=False,
    )

    customer_comment = models.TextField(
        verbose_name=_("Customer comment"),
        help_text=_(
            "If you (the customer) have any comments about the refund please enter them here. This field is not currently being used.",
        ),
        default="",
        blank=True,
    )

    invoice_address = models.TextField(
        help_text=_(
            "The invoice address for this refund. Leave blank to use the invoice address from the Order object.",
        ),
        blank=True,
    )

    notes = models.TextField(
        help_text="Any internal notes about this Refund can be entered here. They will not be printed on the creditnote or shown to the customer in any way.",
        default="",
        blank=True,
    )

    created_by = models.ForeignKey(
        "auth.User",
        help_text="The user who created this refund",
        on_delete=models.PROTECT,
        null=True,  # TODO: Null to support old refunds. Maybe we should have a system user?
        blank=True,  # TODO: Blank to support old refunds. Maybe we should have a system user?
    )

    def save(self, **kwargs):
        """Take the invoice_address for the CreditNote from the Order object if we don't have one."""
        if not self.invoice_address:
            self.invoice_address = self.order.invoice_address
        return super().save(**kwargs)

    def __str__(self):
        return f"Refund #{self.id}"

    @property
    def amount(self):
        return self.rprs.aggregate(
            amount=Sum(
                F("opr__product__price") * F("quantity"),
            ),
        )["amount"]


class RefundProductRelation(CreatedUpdatedModel):
    """The RPR model has an FK to the Refund it belongs to, as well as an FK to the OPR
    it is refunding (partially or fully).

    TODO: Make sure quantity is possible with a constraint
    """

    refund = models.ForeignKey(
        "shop.Refund",
        related_name="rprs",
        on_delete=models.PROTECT,
    )

    opr = models.ForeignKey(
        "shop.OrderProductRelation",
        related_name="rprs",
        help_text="The OPR which this RPR is refunding",
        on_delete=models.PROTECT,
    )

    quantity = models.PositiveIntegerField(
        help_text="The number of times this product is being refunded in this Refund",
    )

    ticket_deleted = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The time when ticket(s) related to this RefundProductRelation were deleted",
    )

    @property
    def total(self):
        """Returns the total price for this RPR considering quantity."""
        return Decimal(self.opr.price * self.quantity)

    def clean(self):
        """Make sure the quantity is not greater than the quantity in the opr."""
        if self.quantity > self.opr.quantity:
            raise ValidationError(
                "The quantity of this RPR cannot be greater than the quantity in the OPR",
            )


# ########## PRODUCTS ################################################


class ProductCategory(
    ExportModelOperationsMixin("product_category"),
    CreatedUpdatedModel,
    UUIDModel,
):
    class Meta:
        verbose_name = "Product category"
        verbose_name_plural = "Product categories"

    name = models.CharField(max_length=150)
    slug = models.SlugField()
    public = models.BooleanField(default=True)
    weight = models.IntegerField(
        default=100,
        help_text="Sorting weight. Heavier items sink to the bottom.",
    )

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        self.slug = unique_slugify(
            self.name,
            slugs_in_use=self.__class__.objects.all().values_list("slug", flat=True),
        )
        super().save(**kwargs)


class ProductStatsManager(models.Manager):
    def with_ticket_stats(self):
        return (
            self.filter(
                orderproductrelation__order__paid=True,
            )
            .annotate(
                total_units_refunded=Coalesce(
                    Sum("orderproductrelation__rprs__quantity"),
                    0,
                ),
            )
            .annotate(
                total_units_sold=Sum("orderproductrelation__quantity")
                - F("total_units_refunded"),
            )
            .exclude(total_units_sold=0)
            .annotate(profit=F("price") - F("cost"))
            .annotate(total_income=F("price") * F("total_units_sold"))
            .annotate(total_cost=F("cost") * F("total_units_sold"))
            .annotate(total_profit=F("profit") * F("total_units_sold"))
            .annotate(paid_order_count=Count("orderproductrelation__order"))
        )


class Product(ExportModelOperationsMixin("product"), CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["available_in", "price", "name"]

    category = models.ForeignKey(
        "shop.ProductCategory",
        related_name="products",
        on_delete=models.PROTECT,
    )

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=100)

    price = models.IntegerField(
        help_text=_("Price of the product (in DKK, including VAT)."),
    )

    description = models.TextField()

    available_in = DateTimeRangeField(
        help_text=_(
            "Which period is this product available for purchase? | "
            "(Format: YYYY-MM-DD HH:MM) | Only one of start/end is required",
        ),
    )

    ticket_type = models.ForeignKey(
        "tickets.TicketType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    ticket_types = models.ManyToManyField(
        "tickets.TicketType",
        through="shop.TicketTypeProductRelation",
        related_name="+",  # todo: temporary
    )

    stock_amount = models.IntegerField(
        help_text=(
            "Initial amount available in stock if there is a limited "
            "supply, e.g. fridge space"
        ),
        null=True,
        blank=True,
    )

    cost = models.IntegerField(
        default=0,
        help_text="The cost for this product, including VAT. Used for profit calculations in the economy system.",
    )

    comment = models.TextField(
        blank=True,
        help_text="Internal comments for this product.",
    )

    objects = ProductQuerySet.as_manager()
    statsobjects = ProductStatsManager()

    def __str__(self):
        return f"{self.name} ({self.price} DKK)"

    def clean(self):
        if self.category.name == "Tickets" and not self.ticket_type:
            raise ValidationError("Products with category Tickets need a ticket_type")

    def is_available(self):
        """Is the product available or not?

        Checks for the following:

        - Whether now is in the self.available_in
        - If a stock is defined, that there are items left
        """
        predicates = [self.is_time_available]
        if self.stock_amount:
            predicates.append(self.is_stock_available)
        return all(predicates)

    @property
    def is_time_available(self):
        now = timezone.now()
        time_available = now in self.available_in
        return time_available

    def is_old(self):
        now = timezone.now()
        if hasattr(self.available_in, "upper") and self.available_in.upper:
            return self.available_in.upper < now
        return False

    def is_upcoming(self):
        now = timezone.now()
        return self.available_in.lower > now

    @property
    def available_for_days(self):
        if self.available_in.upper is not None:
            now = timezone.now()
            return (self.available_in.upper - now).days

    @property
    def left_in_stock(self):
        if self.stock_amount:
            # All orders that are not open and not cancelled count towards what has
            # been "reserved" from stock.
            #
            # This means that an order has either been paid (by card or blockchain)
            # or is marked to be paid with cash or bank transfer, meaning it is a
            # "reservation" of the product in question.
            sold = OrderProductRelation.objects.filter(
                product=self,
                order__open=None,
                order__cancelled=False,
            ).aggregate(Sum("quantity"))["quantity__sum"]

            total_left = self.stock_amount - (sold or 0)

            return total_left
        return None

    @property
    def is_stock_available(self):
        if self.stock_amount:
            stock_available = self.left_in_stock > 0
            return stock_available
        # If there is no stock defined the product is generally available.
        return True


class TicketTypeProductRelation(
    ExportModelOperationsMixin("ticket_type_product_relation"),
    CreatedUpdatedModel,
):
    ticket_type = models.ForeignKey(
        "tickets.TicketType",
        related_name="ttprs",
        on_delete=models.PROTECT,
    )

    product = models.ForeignKey(
        "shop.Product",
        related_name="ttprs",
        on_delete=models.PROTECT,
    )

    number_of_tickets = models.IntegerField(default=1)


class OrderProductRelationQuerySet(models.QuerySet):
    def paid(self):
        return self.filter(order__paid=True)

    def with_refunded(self):
        return self.annotate(
            total_refunded=Sum("rprs__quantity"),
            refunded=Case(
                When(
                    total_refunded=F("quantity"),
                    then=Value(RefundEnum.FULLY_REFUNDED.value),
                ),
                When(
                    total_refunded__gt=0,
                    then=Value(RefundEnum.PARTIALLY_REFUNDED.value),
                ),
                When(
                    total_refunded__isnull=True,
                    then=Value(RefundEnum.NOT_REFUNDED.value),
                ),
            ),
        )

    def not_fully_refunded(self):
        print(self.with_refunded())
        return self.with_refunded().exclude(refunded=RefundEnum.FULLY_REFUNDED.value)

    def not_cancelled(self):
        return self.filter(order__cancelled=False)


class OrderProductRelation(
    ExportModelOperationsMixin("order_product_relation"),
    CreatedUpdatedModel,
):
    def __str__(self):
        return f"#{self.order}: {self.quantity} {self.product}"

    objects = OrderProductRelationQuerySet.as_manager()

    order = models.ForeignKey(
        "shop.Order",
        related_name="oprs",
        on_delete=models.PROTECT,
    )

    product = models.ForeignKey("shop.Product", on_delete=models.PROTECT)

    quantity = models.PositiveIntegerField(
        help_text="The number of times this product has been bought on this order",
    )

    ticket_generated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Generation time of the ticket(s) for this OPR. Blank if ticket(s) have not been generated yet.",
    )

    price = models.IntegerField(
        null=True,
        blank=True,
        help_text=_(
            "The price (per product, at the time of purchase, in DKK, including VAT).",
        ),
    )

    @property
    def total(self):
        """Returns the total price for this OPR considering quantity."""
        return Decimal(self.product.price * self.quantity)

    def create_tickets(self, request=None):
        """This method generates the needed tickets for this OPR.

        We run this in a transaction so everything is undone in case something fails,
        this is better than using djangos autocommit mode, which is only active
        during a request, while transaction.atomic() will also protect against problems
        when calling create_tickets() in manage.py shell or from a worker.

        Calling this method multiple times will not result in duplicate tickets being created,
        and the number of tickets created takes the number of refunded into consideration too.
        """
        tickets = []
        with transaction.atomic():
            # do we even generate tickets for this type of product?
            if not self.product.ticket_types:
                return tickets

            for ticket_type_relation in self.product.ttprs.all():
                ticket_type = ticket_type_relation.ticket_type
                # put reusable kwargs together
                query_kwargs = {
                    "product": self.product,
                    "ticket_type": ticket_type,
                }

                if ticket_type.single_ticket_per_product:
                    # For this ticket type we create one ticket regardless of quantity,
                    # so 20 chairs don't result in 20 tickets

                    # TODO: do ticket_type_relation.number_of_tickets times

                    ticket, created = self.shoptickets.get_or_create(**query_kwargs)

                    if request:
                        if created:
                            msg = f"Created ticket for product {self.product} on order {self.order} (quantity: {self.quantity})"
                            tickets.append(ticket)
                        else:
                            msg = f"Ticket already exists for product {self.product} on order {self.order} (quantity: {self.quantity})"
                            messages.success(request, msg)
                else:
                    # For this ticket type we create a ticket per item,
                    # find out if any have already been created
                    already_created_tickets = self.shoptickets.filter(
                        **query_kwargs,
                    ).count()

                    # find out how many we need to create
                    # TODO: currently we multiply by ticket_type_relation.number_of_tickets
                    #       this is because we have no way of discerning multiple tickets
                    #       created based on ticket_type_relation.number_of_tickets or order_product_relation.quantity.
                    #       Seen from the ticket creation perspective these two numbers have the same function.
                    #       There is no difference between ordering 5 x <product of 1 ticket> and 1 x <product of 5 tickets>.
                    tickets_to_create = (
                        max(
                            0,
                            self.quantity
                            - already_created_tickets
                            - (
                                self.rprs.aggregate(models.Sum("quantity"))[
                                    "quantity__sum"
                                ]
                                or 0
                            ),
                        )
                        * ticket_type_relation.number_of_tickets
                    )

                    if not tickets_to_create:
                        return tickets

                    # create the number of tickets required
                    for _i in range(tickets_to_create):
                        ticket = self.shoptickets.create(**query_kwargs)
                        tickets.append(ticket)

                    if request:
                        msg = f"Created {self.quantity} tickets of type: {ticket_type.name}"
                        messages.success(request, msg)

                # and mark the OPR as ticket_generated=True
                self.ticket_generated = timezone.now()
                self.save()

            return tickets

    @property
    def used_shoptickets(self):
        return self.shoptickets.filter(used_at__isnull=False)

    @property
    def unused_shoptickets(self):
        return self.shoptickets.filter(used_at__isnull=True)

    @property
    def used_tickets_count(self):
        return self.used_shoptickets.count()

    @property
    def refunded_quantity(self):
        return self.rprs.aggregate(refunded=Sum("quantity"))["refunded"] or 0

    @property
    def possible_refund(self):
        quantity = (
            1 if self.product.ticket_type.single_ticket_per_product else self.quantity
        )
        return quantity - self.used_tickets_count - self.refunded_quantity

    @property
    def non_refunded_quantity(self):
        return self.quantity - self.refunded_quantity

    def save(self, **kwargs):
        """Make sure we save the current price in the OPR."""
        if not self.price:
            self.price = self.product.price
        super().save(**kwargs)

    def create_rpr(self, *, refund: Refund, quantity: int):
        return RefundProductRelation.objects.create(
            refund=refund,
            opr=self,
            quantity=quantity,
        )


# ########## EPAY ####################################################


class EpayCallback(
    ExportModelOperationsMixin("epay_callback"),
    CreatedUpdatedModel,
    UUIDModel,
):
    class Meta:
        verbose_name = "Epay Callback"
        verbose_name_plural = "Epay Callbacks"
        ordering = ["-created"]

    payload = models.JSONField()
    md5valid = models.BooleanField(default=False)

    def __str__(self):
        return f"callback at {self.created} (md5 valid: {self.md5valid})"


class EpayPayment(
    ExportModelOperationsMixin("epay_payment"),
    CreatedUpdatedModel,
    UUIDModel,
):
    class Meta:
        verbose_name = "Epay Payment"
        verbose_name_plural = "Epay Payments"
        ordering = ["created"]

    order = models.OneToOneField("shop.Order", on_delete=models.PROTECT)
    callback = models.ForeignKey("shop.EpayCallback", on_delete=models.PROTECT)
    txnid = models.IntegerField()


class CreditNote(ExportModelOperationsMixin("credit_note"), CreatedUpdatedModel):
    class Meta:
        ordering = ["-created"]
        # TODO add a check constraint to ensure that a if a CreditNote has
        # a reference to both an Invoice and a Refund object that the
        # Refund object is related to an Order which related to the same
        # Invoice object

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    text = models.TextField(help_text="Description of what this credit note covers")

    pdf = models.FileField(null=True, blank=True, upload_to="creditnotes/")

    user = models.ForeignKey(
        "auth.User",
        verbose_name=_("User"),
        help_text=_("The user this credit note belongs to, if any."),
        related_name="creditnotes",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    customer = models.TextField(
        help_text="Customer info if no user is selected",
        blank=True,
        default="",
    )

    danish_vat = models.BooleanField(help_text="Danish VAT?", default=True)

    paid = models.BooleanField(
        verbose_name=_("Paid?"),
        help_text=_(
            "Whether the amount in this creditnote has been paid back to the customer.",
        ),
        default=False,
    )

    sent_to_customer = models.BooleanField(default=False)

    invoice = models.ForeignKey(
        "shop.Invoice",
        related_name="creditnotes",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="The Invoice this CreditNote relates to, if any.",
    )

    refund = models.OneToOneField(
        "shop.Refund",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="The Refund this CreditNote relates to, if any.",
    )

    def clean(self):
        errors = []
        if self.user and self.customer:
            msg = "Customer info should be blank if a user is selected."
            errors.append(ValidationError({"user", msg}))
            errors.append(ValidationError({"customer", msg}))
        if not self.user and not self.customer:
            msg = "Either pick a user or fill in Customer info"
            errors.append(ValidationError({"user", msg}))
            errors.append(ValidationError({"customer", msg}))
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        if self.user:
            return "creditnote#{} - {} DKK (customer: user {})".format(
                self.id,
                self.amount,
                self.user.email,
            )
        else:
            return "creditnote#{} - {} DKK (customer: {})".format(
                self.id,
                self.amount,
                self.customer,
            )

    @property
    def vat(self):
        if self.danish_vat:
            return Decimal(round(self.amount * Decimal(0.2), 2))
        else:
            return 0

    @property
    def filename(self):
        return "bornhack_creditnote_%s.pdf" % self.pk


class Invoice(ExportModelOperationsMixin("invoice"), CreatedUpdatedModel):
    order = models.OneToOneField(
        "shop.Order",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    customorder = models.OneToOneField(
        "shop.CustomOrder",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    pdf = models.FileField(null=True, blank=True, upload_to="invoices/")
    sent_to_customer = models.BooleanField(default=False)

    def __str__(self):
        if self.order:
            return "invoice#{} - shop order {} - {} - total {} DKK (sent to {}: {})".format(
                self.id,
                self.order.id,
                self.order.created,
                self.order.total,
                self.order.user.email,
                self.sent_to_customer,
            )
        elif self.customorder:
            return (
                "invoice#%s - custom order %s - %s - amount %s DKK (customer: %s)"
                % (
                    self.id,
                    self.customorder.id,
                    self.customorder.created,
                    self.customorder.amount,
                    unidecode(self.customorder.customer),
                )
            )

    @property
    def filename(self):
        return "bornhack_invoice_%s.pdf" % self.pk

    def regretdate(self):
        return self.created + timedelta(days=15)

    @property
    def get_order(self):
        if self.order:
            return self.order
        else:
            return self.customorder


# ########## COINIFY #################################################


class CoinifyAPIInvoice(
    ExportModelOperationsMixin("coinify_api_invoice"),
    CreatedUpdatedModel,
):
    coinify_id = models.IntegerField(null=True)
    invoicejson = models.JSONField()
    order = models.ForeignKey(
        "shop.Order",
        related_name="coinify_api_invoices",
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return "coinifyinvoice for order #%s" % self.order.id

    @property
    def expired(self):
        return parse_datetime(self.invoicejson["expire_time"]) < timezone.now()


class CoinifyAPICallback(
    ExportModelOperationsMixin("coinify_api_callback"),
    CreatedUpdatedModel,
):
    headers = models.JSONField()
    payload = models.JSONField(blank=True)
    body = models.TextField(default="")
    order = models.ForeignKey(
        "shop.Order",
        related_name="coinify_api_callbacks",
        on_delete=models.PROTECT,
    )
    authenticated = models.BooleanField(default=False)

    def __str__(self):
        return f"order #{self.order.id} callback at {self.created}"


class CoinifyAPIRequest(
    ExportModelOperationsMixin("coinify_api_request"),
    CreatedUpdatedModel,
):
    order = models.ForeignKey(
        "shop.Order",
        related_name="coinify_api_requests",
        on_delete=models.PROTECT,
    )
    method = models.CharField(max_length=100)
    payload = models.JSONField()
    response = models.JSONField()

    def __str__(self):
        return f"order {self.order.id} api request {self.method}"


# ########## QUICKPAY #################################################

HttpMethods = models.TextChoices("Method", "GET POST PUT PATCH DELETE")


class QuickPayAPIRequest(CreatedUpdatedModel, UUIDModel):
    order = models.ForeignKey(
        "shop.Order",
        related_name="quickpay_api_requests",
        on_delete=models.PROTECT,
    )
    method = models.CharField(
        max_length=10,
        choices=HttpMethods.choices,
        help_text="The HTTP method for this request",
    )
    endpoint = models.TextField(help_text="The API endpoint for this request")
    body = models.JSONField(default=dict)
    headers = models.JSONField(default=dict, null=True, blank=True)
    query = models.JSONField(default=dict, null=True, blank=True)
    response_status_code = models.IntegerField(
        null=True,
        blank=True,
        help_text="The HTTP status code of the API response. This field is empty until we get an API response.",
    )
    response_headers = models.JSONField(
        null=True,
        blank=True,
        help_text="The API response headers. This field remains empty until we get an API response.",
    )
    response_body = models.JSONField(
        null=True,
        blank=True,
        help_text="The API response body. This field remains empty until we get an API response.",
    )

    def __str__(self):
        return (
            f"order {self.order.id} quickpay api request {self.method} {self.endpoint}"
        )

    def create_or_update_object(self):
        """Create or update the QuickPayAPIObject in the response_body."""
        if (
            self.response_body
            and "type" in self.response_body
            and "id" in self.response_body
        ):
            obj, created = QuickPayAPIObject.objects.get_or_create(
                id=self.response_body["id"],
                defaults={
                    "order": self.order,
                    "object_type": self.response_body["type"],
                    "object_body": self.response_body,
                },
            )
            return obj


class QuickPayAPIObject(CreatedUpdatedModel, UUIDModel):
    id = models.IntegerField(help_text="The object ID in QuickPays end", unique=True)
    order = models.ForeignKey(
        "shop.Order",
        related_name="quickpay_api_objects",
        on_delete=models.PROTECT,
    )
    object_type = models.TextField(help_text="The type of this QuickPayAPIObject")
    object_body = models.JSONField(help_text="The body of the QuickPay API object")


class QuickPayAPICallback(CreatedUpdatedModel, UUIDModel):
    qpobject = models.ForeignKey(
        "shop.QuickPayAPIObject",
        related_name="callbacks",
        on_delete=models.PROTECT,
        help_text="The QuickPayAPIObject this callback relates to.",
    )
    headers = models.JSONField(help_text="The HTTP headers of the callback")
    body = models.JSONField(help_text="The JSON body of the callback")
