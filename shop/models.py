from django.db import models
from django.db.models.aggregates import Sum
from django.contrib.postgres.fields import DateTimeRangeField, JSONField
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from bornhack.utils import CreatedUpdatedModel, UUIDModel
from .managers import ProductQuerySet


class Order(CreatedUpdatedModel):

    class Meta:
        unique_together = ('user', 'open')

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

    def get_number_of_items(self):
        return self.products.aggregate(
            sum=Sum('orderproductrelation__quantity')
        )['sum']

    @property
    def vat(self):
        return (self.total/100)*25

    @property
    def total(self):
        return self.products.aggregate(
            sum=Sum(
                models.F('orderproductrelation__product__price') *
                models.F('orderproductrelation__quantity'),
                output_field=models.IntegerField()
            )
        )['sum']


class ProductCategory(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Product category'
        verbose_name_plural = 'Product categories'

    name = models.CharField(max_length=150)
    slug = models.SlugField()

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

    payload = JSONField()


class EpayPayment(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Epay Payment'
        verbose_name_plural = 'Epay Payments'

    order = models.OneToOneField('shop.Order')
    callback = models.ForeignKey('shop.EpayCallback')
    txnid = models.IntegerField()
