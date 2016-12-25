import datetime
from django.db import models
from utils.models import UUIDModel, CreatedUpdatedModel


class Camp(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Camp'
        verbose_name_plural = 'Camps'

    title = models.CharField(
        verbose_name='Title',
        help_text='Title of the camp, ie. Bornhack 2016.',
        max_length=255,
    )

    tagline = models.CharField(
        verbose_name='Tagline',
        help_text='Tagline of the camp, ie. "Initial Commit"',
        max_length=255,
    )

    slug = models.SlugField(
        verbose_name='Url Slug',
        help_text='The url slug to use for this camp'
    )

    buildup_start = models.DateTimeField(
        verbose_name='Buildup Start date',
        help_text='When the camp buildup starts.',
    )

    camp_start = models.DateTimeField(
        verbose_name='Start date',
        help_text='When the camp starts.',
    )

    camp_end = models.DateTimeField(
        verbose_name='End date',
        help_text='When the camp ends.',
    )

    teardown_end = models.DateTimeField(
        verbose_name='Start date',
        help_text='When the camp teardown ends.',
    )

    def __unicode__(self):
        return "%s - %s" % (self.title, self.tagline)


class Expense(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'

    payment_time = models.DateTimeField(
        verbose_name='Expense date/time',
        help_text='The date and time this expense was paid.',
    )

    description = models.CharField(
        verbose_name='Description',
        help_text='What this expense covers.',
        max_length=255,
    )

    dkk_amount = models.DecimalField(
        verbose_name='DKK Amount',
        help_text='The DKK amount of the expense.',
        max_digits=7,
        decimal_places=2,
    )

    receipt = models.ImageField(
        verbose_name='Image of receipt',
        help_text='Upload a scan or image of the receipt',
    )

    refund_user = models.ForeignKey(
        'auth.User',
        verbose_name='Refund user',
        help_text='Which user, if any, covered this expense and should be refunded.',
        null=True,
        blank=True,
    )

    refund_paid = models.BooleanField(
        default=False,
        verbose_name='Refund paid?',
        help_text='Has this expense been refunded to the user?',
    )

