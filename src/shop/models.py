import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.postgres.fields import DateTimeRangeField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count
from django.db.models import F
from django.db.models import Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from unidecode import unidecode

from .managers import OrderQuerySet
from .managers import ProductQuerySet
from tickets.models import ShopTicket
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

    CREDIT_CARD = "credit_card"
    BLOCKCHAIN = "blockchain"
    BANK_TRANSFER = "bank_transfer"
    IN_PERSON = "in_person"

    PAYMENT_METHODS = [CREDIT_CARD, BLOCKCHAIN, BANK_TRANSFER, IN_PERSON]

    PAYMENT_METHOD_CHOICES = [
        (CREDIT_CARD, "Credit card"),
        (BLOCKCHAIN, "Blockchain"),
        (BANK_TRANSFER, "Bank transfer"),
        (IN_PERSON, "In Person"),
    ]

    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default="",
        blank=True,
    )

    cancelled = models.BooleanField(default=False)

    refunded = models.BooleanField(
        verbose_name=_("Refunded?"),
        help_text=_("Whether this order has been refunded."),
        default=False,
    )

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

    def get_epay_callback_url(self, request):
        return (
            "https://"
            + request.get_host()
            + str(reverse_lazy("shop:epay_callback", kwargs={"pk": self.pk}))
        )

    @property
    def description(self):
        return "Order #%s" % self.pk

    def get_absolute_url(self):
        return str(reverse_lazy("shop:order_detail", kwargs={"pk": self.pk}))

    def create_tickets(self, request=None):
        tickets = []
        for order_product in self.orderproductrelation_set.all():
            # if this is a Ticket product?
            if order_product.product.ticket_type:
                query_kwargs = {
                    "product": order_product.product,
                    "ticket_type": order_product.product.ticket_type,
                }

                if order_product.product.ticket_type.single_ticket_per_product:
                    # This ticket type is one where we only create one ticket
                    ticket, created = order_product.shoptickets.get_or_create(
                        **query_kwargs
                    )

                    if created:
                        msg = (
                            "Created ticket for product %s on order %s (quantity: %s)"
                            % (
                                order_product.product,
                                order_product.order.pk,
                                order_product.quantity,
                            )
                        )
                        tickets.append(ticket)
                    else:
                        msg = (
                            "Ticket already created for product {} on order {}".format(
                                order_product.product,
                                order_product.order.pk,
                            )
                        )

                    if request:
                        messages.success(request, msg)
                else:
                    # We should create a number of tickets equal to OrderProductRelation quantity
                    already_created_tickets = order_product.shoptickets.filter(
                        **query_kwargs
                    ).count()
                    tickets_to_create = max(
                        0,
                        order_product.quantity - already_created_tickets,
                    )

                    # create the number of tickets required
                    if tickets_to_create > 0:
                        for _i in range(
                            0,
                            (order_product.quantity - already_created_tickets),
                        ):
                            ticket = order_product.shoptickets.create(**query_kwargs)
                            tickets.append(ticket)

                        msg = "Created {} tickets of type: {}".format(
                            order_product.quantity,
                            order_product.product.ticket_type.name,
                        )
                        if request:
                            messages.success(request, msg)

                # and mark the OPR as ticket_generated=True
                order_product.ticket_generated = True
                order_product.save()

        return tickets

    def mark_as_paid(self, request=None):
        self.paid = True
        self.open = None
        self.create_tickets(request)
        self.save()

    def mark_as_refunded(self, request=None):
        if not self.paid:
            msg = "Order %s is not paid, so cannot mark it as refunded!" % self.pk
            if request:
                messages.error(request, msg)
            else:
                print(msg)
        else:
            self.refunded = True
            # delete any tickets related to this order
            tickets = ShopTicket.objects.filter(opr__order=self)
            if tickets.exists():
                msg = "Order {} marked as refunded, deleting {} tickets...".format(
                    self.pk,
                    tickets.count(),
                )
                if request:
                    messages.success(request, msg)
                else:
                    print(msg)
                tickets.delete()
            else:
                msg = "Order %s marked as refunded, no tickets to delete" % self.pk
                if request:
                    messages.success(request, msg)
                else:
                    print(msg)
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

    def is_not_ticket_generated(self):
        if self.orderproductrelation_set.filter(ticket_generated=True).count() == 0:
            return True
        else:
            return False

    def is_partially_ticket_generated(self):
        if (
            self.orderproductrelation_set.filter(ticket_generated=True).count() != 0
            and self.orderproductrelation_set.filter(ticket_generated=False).count()
            != 0
        ):
            # some products are handed out, others are not
            return True
        else:
            return False

    def is_fully_ticket_generated(self):
        if self.orderproductrelation_set.filter(ticket_generated=False).count() == 0:
            return True
        else:
            return False

    @property
    def ticket_generated_status(self):
        if self.is_not_ticket_generated():
            return "no"
        elif self.is_partially_ticket_generated():
            return "partially"
        elif self.is_fully_ticket_generated():
            return "fully"
        else:
            return False

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


class ProductCategory(
    ExportModelOperationsMixin("product_category"), CreatedUpdatedModel, UUIDModel
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
                orderproductrelation__order__refunded=False,
            )
            .annotate(total_units_sold=Sum("orderproductrelation__quantity"))
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


class OrderProductRelation(
    ExportModelOperationsMixin("order_product_relation"), CreatedUpdatedModel
):
    def __str__(self):
        return f"#{self.order}: {self.quantity} {self.product}"

    order = models.ForeignKey("shop.Order", on_delete=models.PROTECT)
    product = models.ForeignKey("shop.Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    ticket_generated = models.BooleanField(default=False)

    @property
    def total(self):
        return Decimal(self.product.price * self.quantity)

    def clean(self):
        if self.ticket_generated and not self.order.paid:
            raise ValidationError(
                "Product can not be handed out when order is not paid.",
            )


class EpayCallback(
    ExportModelOperationsMixin("epay_callback"), CreatedUpdatedModel, UUIDModel
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
    ExportModelOperationsMixin("epay_payment"), CreatedUpdatedModel, UUIDModel
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


class CoinifyAPIInvoice(
    ExportModelOperationsMixin("coinify_api_invoice"), CreatedUpdatedModel
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
    ExportModelOperationsMixin("coinify_api_callback"), CreatedUpdatedModel
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
    ExportModelOperationsMixin("coinify_api_request"), CreatedUpdatedModel
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
