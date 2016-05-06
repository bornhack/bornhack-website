from django.db import models
from django.contrib.postgres.fields import DateTimeRangeField
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from bornhack.utils import CreatedUpdatedModel, UUIDModel

from .managers import TicketTypeQuerySet


class Ticket(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')

    user = models.ForeignKey(
        'auth.User',
        verbose_name=_('User'),
        help_text=_('The user this ticket belongs to.'),
        related_name='tickets',
    )

    paid = models.BooleanField(
        verbose_name=_('Paid?'),
        help_text=_('Whether the user has paid.'),
        default=False,
    )

    ticket_type = models.ForeignKey(
        'tickets.TicketType',
        verbose_name=_('Ticket type'),
    )

    def __str__(self):
        return '{} ({})'.format(
            self.ticket_type.name,
            self.ticket_type.camp
        )


class TicketType(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = _('Ticket Type')
        verbose_name_plural = _('Ticket Types')
        ordering = ['available_in']

    name = models.CharField(max_length=150)

    camp = models.ForeignKey(
        'camps.Camp',
        verbose_name=_('Camp'),
        help_text=_('The camp this ticket type is for.'),
    )

    price = models.IntegerField(
        help_text=_('Price of the ticket (in DKK).')
    )

    available_in = DateTimeRangeField(
        help_text=_(
            'Which period is this ticket available for purchase? | '
            '(Format: YYYY-MM-DD HH:MM) | Only one of start/end is required'
        )
    )

    objects = TicketTypeQuerySet.as_manager()

    def __str__(self):
        return '{} ({} DKK)'.format(
            self.name,
            self.price,
        )

    def is_available(self):
        now = timezone.now()
        return now in self.available_in
