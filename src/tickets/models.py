import io
import logging
import hashlib
import base64
import qrcode

from utils.models import CreatedUpdatedModel, CampRelatedModel
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from utils.models import (
    UUIDModel,
    CreatedUpdatedModel
)
from utils.pdf import generate_pdf_letter
from django.db import models

logger = logging.getLogger("bornhack.%s" % __name__)


# TicketType can be full week, one day. etc.
class TicketType(CampRelatedModel, UUIDModel):
    name = models.TextField()
    camp = models.ForeignKey('camps.Camp')

    def __str__(self):
        return '{} ({})'.format(self.name, self.camp.title)


class BaseTicket(CreatedUpdatedModel, UUIDModel):
    ticket_type = models.ForeignKey('TicketType')
    checked_in = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def _get_token(self):
        return hashlib.sha256(
            '{_id}{secret_key}'.format(
                _id=self.pk,
                secret_key=settings.SECRET_KEY,
            ).encode('utf-8')
        ).hexdigest()

    def get_qr_code_base64(self):
        qr = qrcode.make(
            self._get_token(),
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H
        ).resize((250, 250))
        file_like = io.BytesIO()
        qr.save(file_like, format='png')
        qrcode_base64 = base64.b64encode(file_like.getvalue())
        return qrcode_base64

    def get_qr_code_url(self):
        return 'data:image/png;base64,{}'.format(self.get_qr_code_base64().decode('utf-8'))

    def generate_pdf(self):
        return generate_pdf_letter(
            filename='{}_ticket_{}.pdf'.format(self.shortname, self.pk),
            formatdict={'ticket': self},
            template='pdf/ticket.html'
        )


class SponsorTicket(BaseTicket):
    sponsor = models.ForeignKey('sponsors.Sponsor')

    def __str__(self):
        return 'SponsorTicket: {}'.format(self.pk)

    @property
    def shortname(self):
        return "sponsor"


class DiscountTicket(BaseTicket):
    price = models.IntegerField(
        help_text=_('Price of the discounted ticket (in DKK, including VAT).')
    )

    def __str__(self):
        return 'DiscountTicket: {}'.format(self.pk)

    @property
    def shortname(self):
        return "discount"

class ShopTicket(BaseTicket):
    order = models.ForeignKey('shop.Order', related_name='shoptickets')
    product = models.ForeignKey('shop.Product')

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

    # overwrite the _get_token method because old tickets use the user_id
    def _get_token(self):
        return hashlib.sha256(
            '{_id}{user_id}{secret_key}'.format(
                _id=self.pk,
                user_id=self.order.user.pk,
                secret_key=settings.SECRET_KEY,
            ).encode('utf-8')
        ).hexdigest()

    def __str__(self):
        return 'Ticket {user} {product}'.format(
            user=self.order.user,
            product=self.product
        )

    def get_absolute_url(self):
        return str(
            reverse_lazy('tickets:shopticket_edit', kwargs={'pk': self.pk})
        )

    @property
    def shortname(self):
        return "shop"

