import logging

from django.conf import settings
from django.db import models
from django.db.models.aggregates import Sum
from django.contrib import messages
from django.contrib.postgres.fields import DateTimeRangeField, JSONField
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta
from unidecode import unidecode
from django.utils.dateparse import parse_datetime

from utils.models import UUIDModel, CreatedUpdatedModel
from .managers import ProductQuerySet, OrderQuerySet

logger = logging.getLogger("bornhack.%s" % __name__)


class CustomOrder(CreatedUpdatedModel):
    text = models.TextField(help_text=_("The invoice text"))

    customer = models.TextField(help_text=_("The customer info for this order"))

    amount = models.IntegerField(
        help_text=_("Amount of this custom order (in DKK, including VAT).")
    )

    paid = models.BooleanField(
        verbose_name=_("Paid?"),
        help_text=_(
            "Check when this custom order has been paid (or if it gets cancelled out by a Credit Note)"
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


class Order(CreatedUpdatedModel):
    class Meta:
        unique_together = ("user", "open")
        ordering = ["-created"]

    products = models.ManyToManyField(
        "shop.Product", through="shop.OrderProductRelation"
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

    # We are using a NullBooleanField here to ensure that we only have one open order per user at a time.
    # This "hack" is possible since postgres treats null values as different, and thus we have database level integrity.
    open = models.NullBooleanField(
        verbose_name=_("Open?"),
        help_text=_('Whether this shop order is open or not. "None" means closed.'),
        default=True,
    )

    CREDIT_CARD = "credit_card"
    BLOCKCHAIN = "blockchain"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"

    PAYMENT_METHODS = [CREDIT_CARD, BLOCKCHAIN, BANK_TRANSFER, CASH]

    PAYMENT_METHOD_CHOICES = [
        (CREDIT_CARD, "Credit card"),
        (BLOCKCHAIN, "Blockchain"),
        (BANK_TRANSFER, "Bank transfer"),
        (CASH, "Cash"),
    ]

    payment_method = models.CharField(
        max_length=50, choices=PAYMENT_METHOD_CHOICES, default="", blank=True
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
            "The invoice address for this order. Leave blank to use the email associated with the logged in user."
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
                    )
                )["sum"]
            )
        else:
            return False

    def get_coinify_callback_url(self, request):
        """ Check settings for an alternative COINIFY_CALLBACK_HOSTNAME otherwise use the one from the request """
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
                query_kwargs = dict(
                    product=order_product.product,
                    ticket_type=order_product.product.ticket_type,
                )

                if order_product.product.ticket_type.single_ticket_per_product:
                    # This ticket type is one where we only create one ticket
                    ticket, created = self.shoptickets.get_or_create(**query_kwargs)

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
                        msg = "Ticket already created for product %s on order %s" % (
                            order_product.product,
                            order_product.order.pk,
                        )

                    if request:
                        messages.success(request, msg)
                else:
                    # We should create a number of tickets equal to OrderProductRelation quantity
                    already_created_tickets = self.shoptickets.filter(
                        **query_kwargs
                    ).count()
                    tickets_to_create = max(
                        0, order_product.quantity - already_created_tickets
                    )

                    # create the number of tickets required
                    if tickets_to_create > 0:
                        for _ in range(
                            0, (order_product.quantity - already_created_tickets)
                        ):
                            ticket = self.shoptickets.create(**query_kwargs)
                            tickets.append(ticket)

                        msg = "Created %s tickets of type: %s" % (
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
            if self.shoptickets.all():
                msg = "Order %s marked as refunded, deleting %s tickets..." % (
                    self.pk,
                    self.shoptickets.count(),
                )
                if request:
                    messages.success(request, msg)
                else:
                    print(msg)
                self.shoptickets.all().delete()
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


class ProductCategory(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = "Product category"
        verbose_name_plural = "Product categories"

    name = models.CharField(max_length=150)
    slug = models.SlugField()
    public = models.BooleanField(default=True)
    weight = models.IntegerField(
        default=100, help_text="Sorting weight. Heavier items sink to the bottom."
    )

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        self.slug = slugify(self.name)
        super(ProductCategory, self).save(**kwargs)


class Product(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["available_in", "price", "name"]

    category = models.ForeignKey(
        "shop.ProductCategory", related_name="products", on_delete=models.PROTECT
    )

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=100)

    price = models.IntegerField(
        help_text=_("Price of the product (in DKK, including VAT).")
    )

    description = models.TextField()

    available_in = DateTimeRangeField(
        help_text=_(
            "Which period is this product available for purchase? | "
            "(Format: YYYY-MM-DD HH:MM) | Only one of start/end is required"
        )
    )

    ticket_type = models.ForeignKey(
        "tickets.TicketType", on_delete=models.PROTECT, null=True, blank=True
    )

    stock_amount = models.IntegerField(
        help_text=(
            "Initial amount available in stock if there is a limited "
            "supply, e.g. fridge space"
        ),
        null=True,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    def __str__(self):
        return "{} ({} DKK)".format(self.name, self.price)

    def clean(self):
        if self.category.name == "Tickets" and not self.ticket_type:
            raise ValidationError("Products with category Tickets need a ticket_type")

    def is_available(self):
        """ Is the product available or not?

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
    def left_in_stock(self):
        if self.stock_amount:
            # All orders that are not open and not cancelled count towards what has
            # been "reserved" from stock.
            #
            # This means that an order has either been paid (by card or blockchain)
            # or is marked to be paid with cash or bank transfer, meaning it is a
            # "reservation" of the product in question.
            sold = OrderProductRelation.objects.filter(
                product=self, order__open=None, order__cancelled=False
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


class OrderProductRelation(CreatedUpdatedModel):
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
                "Product can not be handed out when order is not paid."
            )


class EpayCallback(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = "Epay Callback"
        verbose_name_plural = "Epay Callbacks"
        ordering = ["-created"]

    payload = JSONField()
    md5valid = models.BooleanField(default=False)

    def __str__(self):
        return "callback at %s (md5 valid: %s)" % (self.created, self.md5valid)


class EpayPayment(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = "Epay Payment"
        verbose_name_plural = "Epay Payments"

    order = models.OneToOneField("shop.Order", on_delete=models.PROTECT)
    callback = models.ForeignKey("shop.EpayCallback", on_delete=models.PROTECT)
    txnid = models.IntegerField()


class CreditNote(CreatedUpdatedModel):
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
        help_text="Customer info if no user is selected", blank=True, default=""
    )

    danish_vat = models.BooleanField(help_text="Danish VAT?", default=True)

    paid = models.BooleanField(
        verbose_name=_("Paid?"),
        help_text=_(
            "Whether the amount in this creditnote has been paid back to the customer."
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
            return "creditnoote#%s - %s DKK (customer: user %s)" % (
                self.id,
                self.amount,
                self.user.email,
            )
        else:
            return "creditnoote#%s - %s DKK (customer: %s)" % (
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


class Invoice(CreatedUpdatedModel):
    order = models.OneToOneField(
        "shop.Order", null=True, blank=True, on_delete=models.PROTECT
    )
    customorder = models.OneToOneField(
        "shop.CustomOrder", null=True, blank=True, on_delete=models.PROTECT
    )
    pdf = models.FileField(null=True, blank=True, upload_to="invoices/")
    sent_to_customer = models.BooleanField(default=False)

    def __str__(self):
        if self.order:
            return "invoice#%s - shop order %s - %s - total %s DKK (sent to %s: %s)" % (
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


class CoinifyAPIInvoice(CreatedUpdatedModel):
    coinify_id = models.IntegerField(null=True)
    invoicejson = JSONField()
    order = models.ForeignKey(
        "shop.Order", related_name="coinify_api_invoices", on_delete=models.PROTECT
    )

    def __str__(self):
        return "coinifyinvoice for order #%s" % self.order.id

    @property
    def expired(self):
        return parse_datetime(self.invoicejson["expire_time"]) < timezone.now()


class CoinifyAPICallback(CreatedUpdatedModel):
    headers = JSONField()
    payload = JSONField(blank=True)
    body = models.TextField(default="")
    order = models.ForeignKey(
        "shop.Order", related_name="coinify_api_callbacks", on_delete=models.PROTECT
    )
    authenticated = models.BooleanField(default=False)

    def __str__(self):
        return "order #%s callback at %s" % (self.order.id, self.created)


class CoinifyAPIRequest(CreatedUpdatedModel):
    order = models.ForeignKey(
        "shop.Order", related_name="coinify_api_requests", on_delete=models.PROTECT
    )
    method = models.CharField(max_length=100)
    payload = JSONField()
    response = JSONField()

    def __str__(self):
        return "order %s api request %s" % (self.order.id, self.method)
