import io
import logging
import hashlib
import base64
import qrcode

from django.conf import settings
from django.db import models
from django.db.models.aggregates import Sum
from django.contrib import messages
from django.contrib.postgres.fields import DateTimeRangeField, JSONField
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.urlresolvers import reverse_lazy
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta
from unidecode import unidecode
from django.utils.dateparse import parse_datetime

from utils.models import UUIDModel, CreatedUpdatedModel
from tickets.models import ShopTicket
from .managers import ProductQuerySet, OrderQuerySet

logger = logging.getLogger("bornhack.%s" % __name__)


class CustomOrder(CreatedUpdatedModel):
    text = models.TextField(
        help_text=_('The invoice text')
    )

    customer = models.TextField(
        help_text=_('The customer info for this order')
    )

    amount = models.IntegerField(
        help_text=_('Amount of this custom order (in DKK, including VAT).')
    )

    paid = models.BooleanField(
        verbose_name=_('Paid?'),
        help_text=_('Check when this custom order has been paid (or if it gets cancelled out by a Credit Note)'),
        default=False,
    )

    danish_vat = models.BooleanField(
        help_text="Danish VAT?",
        default=True
    )

    def __str__(self):
        return 'custom order id #%s' % self.pk

    @property
    def vat(self):
        if self.danish_vat:
            return Decimal(round(self.amount*Decimal(0.2), 2))
        else:
            return 0


class Order(CreatedUpdatedModel):
    class Meta:
        unique_together = ('user', 'open')
        ordering = ['-created']

    products = models.ManyToManyField(
        'shop.Product',
        through='shop.OrderProductRelation'
    )

    user = models.ForeignKey(
        'auth.User',
        verbose_name=_('User'),
        help_text=_('The user this shop order belongs to.'),
        related_name='orders',
    )

    paid = models.BooleanField(
        verbose_name=_('Paid?'),
        help_text=_('Whether this shop order has been paid.'),
        default=False,
    )

    open = models.NullBooleanField(
        verbose_name=_('Open?'),
        help_text=_('Whether this shop order is open or not. "None" means closed.'),
        default=True,
    )

    CREDIT_CARD = 'credit_card'
    BLOCKCHAIN = 'blockchain'
    BANK_TRANSFER = 'bank_transfer'
    CASH = 'cash'

    PAYMENT_METHODS = [
        CREDIT_CARD,
        BLOCKCHAIN,
        BANK_TRANSFER,
        CASH,
    ]

    PAYMENT_METHOD_CHOICES = [
        (CREDIT_CARD, 'Credit card'),
        (BLOCKCHAIN, 'Blockchain'),
        (BANK_TRANSFER, 'Bank transfer'),
        (CASH, 'Cash'),
    ]

    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default='',
        blank=True
    )

    cancelled = models.BooleanField(default=False)

    refunded = models.BooleanField(
        verbose_name=_('Refunded?'),
        help_text=_('Whether this order has been refunded.'),
        default=False,
    )

    customer_comment = models.TextField(
        verbose_name=_('Customer comment'),
        help_text=_('If you have any comments about the order please enter them here.'),
        default='',
        blank=True,
    )

    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return 'shop order id #%s' % self.pk

    def get_number_of_items(self):
        return self.products.aggregate(
            sum=Sum('orderproductrelation__quantity')
        )['sum']

    @property
    def vat(self):
        return Decimal(self.total*Decimal(0.2))

    @property
    def total(self):
        if self.products.all():
            return Decimal(self.products.aggregate(
                sum=Sum(
                    models.F('orderproductrelation__product__price') *
                    models.F('orderproductrelation__quantity'),
                    output_field=models.IntegerField()
                )
            )['sum'])
        else:
            return False

    def get_coinify_callback_url(self, request):
        """ Check settings for an alternative COINIFY_CALLBACK_HOSTNAME otherwise use the one from the request """
        if hasattr(settings, 'COINIFY_CALLBACK_HOSTNAME') and settings.COINIFY_CALLBACK_HOSTNAME:
            host = settings.COINIFY_CALLBACK_HOSTNAME
        else:
            host = request.get_host()
        return 'https://' + host + str(reverse_lazy('shop:coinify_callback', kwargs={'pk': self.pk}))

    def get_coinify_thanks_url(self, request):
        return 'https://' + request.get_host() + str(reverse_lazy('shop:coinify_thanks', kwargs={'pk': self.pk}))

    def get_epay_accept_url(self, request):
        return 'https://' + request.get_host() + str(reverse_lazy('shop:epay_thanks', kwargs={'pk': self.pk}))

    def get_cancel_url(self, request):
        return 'https://' + request.get_host() + str(reverse_lazy('shop:order_detail', kwargs={'pk': self.pk}))

    def get_epay_callback_url(self, request):
        return 'https://' + request.get_host() + str(reverse_lazy('shop:epay_callback', kwargs={'pk': self.pk}))

    @property
    def description(self):
        return "Order #%s" % self.pk

    def get_absolute_url(self):
        return str(reverse_lazy('shop:order_detail', kwargs={'pk': self.pk}))

    def mark_as_paid(self):
        self.paid = True
        self.open = None
        for order_product in self.orderproductrelation_set.all():
            if order_product.product.category.name == "Tickets":
                for _ in range(0, order_product.quantity):
                    ticket = ShopTicket(
                        ticket_type=order_product.product.ticket_type,
                        order=self,
                        product=order_product.product,
                    )
                    ticket.save()
        self.save()

    def mark_as_refunded(self, request):
        if not self.paid:
            messages.error(request, "Order %s is not paid, so cannot mark it as refunded!" % self.pk)
        else:
            self.refunded=True
            ### delete any tickets related to this order
            if self.tickets.all():
                messages.success(request, "Order %s marked as refunded, deleting %s tickets..." % (self.pk, self.tickets.count()))
                self.tickets.all().delete()
            else:
                messages.success(request, "Order %s marked as refunded, no tickets to delete" % self.pk)
            self.save()

    def is_not_handed_out(self):
        if self.orderproductrelation_set.filter(handed_out=True).count() == 0:
            return True
        else:
            return False

    def is_partially_handed_out(self):
        if self.orderproductrelation_set.filter(handed_out=True).count() != 0 and self.orderproductrelation_set.filter(handed_out=False).count() != 0:
            # some products are handed out, others are not
            return True
        else:
            return False

    def is_fully_handed_out(self):
        if self.orderproductrelation_set.filter(handed_out=False).count() == 0:
            return True
        else:
            return False

    @property
    def handed_out_status(self):
        if self.is_not_handed_out():
            return "no"
        elif self.is_partially_handed_out():
            return "partially"
        elif self.is_fully_handed_out():
            return "fully"
        else:
            return False

    def mark_as_cancelled(self):
        self.cancelled = True
        self.open = None
        self.save()

    @property
    def coinifyapiinvoice(self):
        if not self.coinify_api_invoices.exists():
            return False

        coinifyinvoice = None
        for tempinvoice in self.coinify_api_invoices.all():
            # we already have a coinifyinvoice for this order, check if it expired
            if not tempinvoice.expired:
                # this invoice is not expired, we are good to go
                return tempinvoice

        # nope
        return False


class ProductCategory(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Product category'
        verbose_name_plural = 'Product categories'

    name = models.CharField(max_length=150)
    slug = models.SlugField()
    public = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        self.slug = slugify(self.name)
        super(ProductCategory, self).save(**kwargs)


class Product(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['available_in', 'price', 'name']

    category = models.ForeignKey(
        'shop.ProductCategory',
        related_name='products'
    )

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, max_length=100)

    price = models.IntegerField(
        help_text=_('Price of the product (in DKK, including VAT).')
    )

    description = models.TextField()

    available_in = DateTimeRangeField(
        help_text=_(
            'Which period is this product available for purchase? | '
            '(Format: YYYY-MM-DD HH:MM) | Only one of start/end is required'
        )
    )

    ticket_type = models.ForeignKey(
        'tickets.TicketType',
        null=True,
        blank=True
    )

    objects = ProductQuerySet.as_manager()

    def __str__(self):
        return '{} ({} DKK)'.format(
            self.name,
            self.price,
        )

    def clean(self):
        if self.category.name == 'Tickets' and not self.ticket_type:
            raise ValidationError(
                'Products with category Tickets need a ticket_type'
            )

    def is_available(self):
        now = timezone.now()
        return now in self.available_in

    def is_old(self):
        now = timezone.now()
        if hasattr(self.available_in, 'upper') and self.available_in.upper:
            return self.available_in.upper < now
        return False

    def is_upcoming(self):
        now = timezone.now()
        return self.available_in.lower > now


class OrderProductRelation(CreatedUpdatedModel):
    order = models.ForeignKey('shop.Order')
    product = models.ForeignKey('shop.Product')
    quantity = models.PositiveIntegerField()
    handed_out = models.BooleanField(default=False)

    @property
    def total(self):
        return Decimal(self.product.price * self.quantity)


class EpayCallback(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Epay Callback'
        verbose_name_plural = 'Epay Callbacks'
        ordering = ['-created']

    payload = JSONField()
    md5valid = models.BooleanField(default=False)

    def __str__(self):
        return 'callback at %s (md5 valid: %s)' % (self.created, self.md5valid)


class EpayPayment(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Epay Payment'
        verbose_name_plural = 'Epay Payments'

    order = models.OneToOneField('shop.Order')
    callback = models.ForeignKey('shop.EpayCallback')
    txnid = models.IntegerField()


class CreditNote(CreatedUpdatedModel):
    class Meta:
        ordering = ['-created']

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    text = models.TextField(
        help_text="Description of what this credit note covers"
    )

    pdf = models.FileField(
        null=True,
        blank=True,
        upload_to='creditnotes/'
    )

    user = models.ForeignKey(
        'auth.User',
        verbose_name=_('User'),
        help_text=_('The user this credit note belongs to, if any.'),
        related_name='creditnotes',
        null=True,
        blank=True
    )

    customer = models.TextField(
        help_text="Customer info if no user is selected",
        blank=True,
        default='',
    )

    danish_vat = models.BooleanField(
        help_text="Danish VAT?",
        default=True
    )

    paid = models.BooleanField(
        verbose_name=_('Paid?'),
        help_text=_('Whether the amount in this creditnote has been paid back to the customer.'),
        default=False,
    )

    sent_to_customer = models.BooleanField(default=False)

    def clean(self):
        errors = []
        if self.user and self.customer:
            msg = "Customer info should be blank if a user is selected."
            errors.append(ValidationError({'user', msg}))
            errors.append(ValidationError({'customer', msg}))
        if not self.user and not self.customer:
            msg = "Either pick a user or fill in Customer info"
            errors.append(ValidationError({'user', msg}))
            errors.append(ValidationError({'customer', msg}))
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        if self.user:
            return 'creditnoote#%s - %s DKK (customer: user %s)' % (
                self.id,
                self.amount,
                self.user.email,
            )
        else:
            return 'creditnoote#%s - %s DKK (customer: %s)' % (
                self.id,
                self.amount,
                self.customer,
            )

    @property
    def vat(self):
        if self.danish_vat:
            return Decimal(round(self.amount*Decimal(0.2), 2))
        else:
            return 0

    @property
    def filename(self):
        return 'bornhack_creditnote_%s.pdf' % self.pk


class Invoice(CreatedUpdatedModel):
    order = models.OneToOneField('shop.Order', null=True, blank=True)
    customorder = models.OneToOneField('shop.CustomOrder', null=True, blank=True)
    pdf = models.FileField(null=True, blank=True, upload_to='invoices/')
    sent_to_customer = models.BooleanField(default=False)

    def __str__(self):
        if self.order:
            return 'invoice#%s - shop order %s - %s - total %s DKK (sent to %s: %s)' % (
                self.id,
                self.order.id,
                self.order.created,
                self.order.total,
                self.order.user.email,
                self.sent_to_customer,
            )
        elif self.customorder:
            return 'invoice#%s - custom order %s - %s - amount %s DKK (customer: %s)' % (
                self.id,
                self.customorder.id,
                self.customorder.created,
                self.customorder.amount,
                unidecode(self.customorder.customer),
            )

    @property
    def filename(self):
        return 'bornhack_invoice_%s.pdf' % self.pk

    def regretdate(self):
        return self.created+timedelta(days=15)


class CoinifyAPIInvoice(CreatedUpdatedModel):
    coinify_id = models.IntegerField(null=True)
    invoicejson = JSONField()
    order = models.ForeignKey('shop.Order', related_name="coinify_api_invoices", on_delete=models.PROTECT)

    def __str__(self):
        return "coinifyinvoice for order #%s" % self.order.id

    @property
    def expired(self):
         return parse_datetime(self.invoicejson['expire_time']) < timezone.now()


class CoinifyAPICallback(CreatedUpdatedModel):
    headers = JSONField()
    payload = JSONField(blank=True)
    body = models.TextField(default='')
    order = models.ForeignKey('shop.Order', related_name="coinify_api_callbacks", on_delete=models.PROTECT)
    authenticated = models.BooleanField(default=False)

    def __str__(self):
        return 'order #%s callback at %s' % (self.order.id, self.created)


class CoinifyAPIRequest(CreatedUpdatedModel):
    order = models.ForeignKey('shop.Order', related_name="coinify_api_requests", on_delete=models.PROTECT)
    method = models.CharField(max_length=100)
    payload = JSONField()
    response = JSONField()

    def __str__(self):
        return 'order %s api request %s' % (self.order.id, self.method)


class Ticket(CreatedUpdatedModel, UUIDModel):
    order = models.ForeignKey('shop.Order', related_name='tickets')
    product = models.ForeignKey('shop.Product', related_name='tickets')
    qrcode_base64 = models.TextField(null=True, blank=True)

    name = models.CharField(
        max_length=100,
        help_text=(
            'Name of the person this ticket belongs to. '
            'This can be different from the buying user.'
        ),
        null=True,
        blank=True,
    )

    email = models.EmailField(
        null=True,
        blank=True,
    )

    checked_in = models.BooleanField(default=False)

    def __str__(self):
        return 'Ticket {user} {product}'.format(
            user=self.order.user,
            product=self.product
        )

    def save(self, **kwargs):
        super(Ticket, self).save(**kwargs)
        self.qrcode_base64 = self.get_qr_code()
        super(Ticket, self).save(**kwargs)

    def get_token(self):
        return hashlib.sha256(
            '{ticket_id}{user_id}{secret_key}'.format(
                ticket_id=self.pk,
                user_id=self.order.user.pk,
                secret_key=settings.SECRET_KEY,
            ).encode('utf-8')
        ).hexdigest()

    def get_qr_code(self):
        qr = qrcode.make(
            self.get_token(),
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H
        ).resize((250,250))
        file_like = io.BytesIO()
        qr.save(file_like, format='png')
        qrcode_base64 = base64.b64encode(file_like.getvalue())
        return qrcode_base64

    def get_qr_code_url(self):
        return 'data:image/png;base64,{}'.format(self.qrcode_base64)

    def get_absolute_url(self):
        return str(reverse_lazy('shop:ticket_detail', kwargs={'pk': self.pk}))
