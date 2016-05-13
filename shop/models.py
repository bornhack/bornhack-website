from django.db import models
from django.contrib.postgres.fields import DateTimeRangeField, JSONField
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from bornhack.utils import CreatedUpdatedModel, UUIDModel
from .managers import ProductQuerySet


class Order(CreatedUpdatedModel):

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

    finalized = models.BooleanField(
        verbose_name=_('Finalized?'),
        help_text=_('Whether this order has been finalized.'),
        default=False,
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
        (CREDIT_CARD, 'Credit card'),
        (BLOCKCHAIN, 'Blockchain'),
        (BANK_TRANSFER, 'Bank transfer'),
    ]

    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHODS,
        default=BLOCKCHAIN
    )


class ProductCategory(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Product category'
        verbose_name_plural = 'Product categories'

    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Product(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['available_in']

    category = models.ForeignKey('shop.ProductCategory')

    name = models.CharField(max_length=150)

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

    def is_available(self):
        now = timezone.now()
        return now in self.available_in


class OrderProductRelation(models.Model):
    order = models.ForeignKey('shop.Order')
    product = models.ForeignKey('shop.Product')
    quantity = models.PositiveIntegerField()
    handed_out = models.BooleanField(default=False)


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
