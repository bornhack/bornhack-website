from django.conf import settings
from django.db import models
from django.db.models.aggregates import Sum
from django.contrib.postgres.fields import DateTimeRangeField, JSONField
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.urlresolvers import reverse_lazy
from utils.models import UUIDModel, CreatedUpdatedModel
from .managers import ProductQuerySet
import hashlib, io, base64, qrcode
from decimal import Decimal


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
        help_text=_('The user this order belongs to.'),
        related_name='orders',
    )

    paid = models.BooleanField(
        verbose_name=_('Paid?'),
        help_text=_('Whether this order has been paid.'),
        default=False,
    )

    open = models.NullBooleanField(
        verbose_name=_('Open?'),
        help_text=_('Whether this order is open or not. "None" means closed.'),
        default=True,
    )

    camp = models.ForeignKey(
        'camps.Camp',
        verbose_name=_('Camp'),
        help_text=_('The camp this order is for.'),
    )

    CREDIT_CARD = 'credit_card'
    BLOCKCHAIN = 'blockchain'
    BANK_TRANSFER = 'bank_transfer'

    PAYMENT_METHODS = [
        CREDIT_CARD,
        BLOCKCHAIN,
        BANK_TRANSFER,
    ]

    PAYMENT_METHOD_CHOICES = [
        (CREDIT_CARD, 'Credit card'),
        (BLOCKCHAIN, 'Blockchain'),
        (BANK_TRANSFER, 'Bank transfer'),
    ]

    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default=BLOCKCHAIN
    )

    def __str__(self):
        return 'order id #%s' % self.pk

    def get_number_of_items(self):
        return self.products.aggregate(
            sum=Sum('orderproductrelation__quantity')
        )['sum']

    @property
    def vat(self):
        return Decimal(self.total*0.2)

    @property
    def total(self):
        return Decimal(self.products.aggregate(
            sum=Sum(
                models.F('orderproductrelation__product__price') *
                models.F('orderproductrelation__quantity'),
                output_field=models.IntegerField()
            )
        )['sum'])

    def get_coinify_callback_url(self, request):
        return 'https://' + request.get_host() + str(reverse_lazy('shop:coinify_callback', kwargs={'pk': self.pk}))

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
        return "BornHack %s order #%s" % (self.camp.start.year, self.pk)

    def get_absolute_url(self):
        return str(reverse_lazy('shop:order_detail', kwargs={'pk': self.pk}))

    def mark_as_paid(self):
        self.paid = True
        for order_product in self.orderproductrelation_set.all():
            category_pk = str(order_product.product.category.pk)
            print(order_product, category_pk, settings.TICKET_CATEGORY_ID)
            if category_pk == settings.TICKET_CATEGORY_ID:
                for _ in range(0, order_product.quantity):
                    ticket = Ticket(
                        order=self,
                        product=order_product.product,
                    )
                    ticket.save()
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
        ordering = ['available_in']

    category = models.ForeignKey(
        'shop.ProductCategory',
        related_name='products'
    )

    name = models.CharField(max_length=150)
    slug = models.SlugField()

    price = models.IntegerField(
        help_text=_('Price of the product (in DKK).')
    )

    description = models.TextField()

    available_in = DateTimeRangeField(
        help_text=_(
            'Which period is this product available for purchase? | '
            '(Format: YYYY-MM-DD HH:MM) | Only one of start/end is required'
        )
    )
    
    objects = ProductQuerySet.as_manager()

    def __str__(self):
        return '{} ({} DKK)'.format(
            self.name,
            self.price,
        )

    def save(self, **kwargs):
        self.slug = slugify(self.name)
        super(Product, self).save(**kwargs)

    def is_available(self):
        now = timezone.now()
        return now in self.available_in


class OrderProductRelation(CreatedUpdatedModel):
    order = models.ForeignKey('shop.Order')
    product = models.ForeignKey('shop.Product')
    quantity = models.PositiveIntegerField()
    handed_out = models.BooleanField(default=False)

    @property
    def total(self):
        return self.product.price * self.quantity


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


class Invoice(CreatedUpdatedModel):
    order = models.OneToOneField('shop.Order')
    pdf = models.FileField(null=True, blank=True, upload_to='invoices/')
    sent_to_customer = models.BooleanField(default=False)

    def __str__(self):
        return 'invoice#%s - order %s - %s - total %s DKK (sent to customer: %s)' % (
            self.id,
            self.order.id,
            self.order.created,
            self.order.total,
            self.sent_to_customer,
        )

    @property
    def filename(self):
        return 'bornhack_invoice_%s.pdf' % self.pk

    def regretdate(self):
        return inv.created+timedelta(days=14)

class CoinifyAPIInvoice(CreatedUpdatedModel):
    invoicejson = JSONField()
    order = models.OneToOneField('shop.Order')


class CoinifyAPICallback(CreatedUpdatedModel):
    headers = JSONField()
    payload = JSONField()
    order = models.ForeignKey('shop.Order')
    valid = models.BooleanField(default=False)

    def __str__(self):
        return 'order #%s callback at %s' % (self.order.id, self.created)


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
            )
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
