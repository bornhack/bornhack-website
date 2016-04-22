from django.db import models
from django.contrib.postgres.fields import DateTimeRangeField
from django.utils.translation import ugettext_lazy as _

from bornhack.utils import CreatedUpdatedModel, UUIDModel


class Ticket(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')

    camp = models.ForeignKey(
        'camps.Camp',
        verbose_name=_('Camp'),
        help_text=_('The camp this ticket is for.'),
    )

    user = models.ForeignKey(
        'auth.User',
        verbose_name=_('User'),
        help_text=_('The user this ticket belongs to.'),
    )

    paid = models.BooleanField(
        verbose_name=_('Paid?'),
        help_text=_('Whether the user has paid.'),
        default=False,
    )

    ticket_type = models.ForeignKey(
        'tickets.TicketType',
        verbose_name=_('Ticket type'),
        help_text=_('The type of the ticket.'),
    )


class TicketType(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = _('Ticket Type')
        verbose_name_plural = _('Ticket Types')

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
        help_text=_('Which period is this ticket available for purchase?')
    )

    def __str__(self):
        return self.name
