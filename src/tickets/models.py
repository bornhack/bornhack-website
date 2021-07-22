import base64
import hashlib
import io
import logging

import qrcode
from django.conf import settings
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from shop.models import OrderProductRelation
from utils.models import CampRelatedModel, UUIDModel
from utils.pdf import generate_pdf_letter

logger = logging.getLogger("bornhack.%s" % __name__)


class TicketTypeManager(models.Manager):
    def with_price_stats(self):
        return self.annotate(shopticket_count=models.Count("shopticket")).exclude(
            shopticket_count=0
        )


# TicketType can be full week, one day, cabins, parking, merch, hax, massage, etc.
class TicketType(CampRelatedModel, UUIDModel):
    objects = TicketTypeManager()
    name = models.TextField()
    camp = models.ForeignKey("camps.Camp", on_delete=models.PROTECT)
    includes_badge = models.BooleanField(default=False)
    single_ticket_per_product = models.BooleanField(
        default=False,
        help_text=(
            "Only create one ticket for a product/order pair no matter the quantity. "
            "Useful for products which are bought in larger quantity (ie. village chairs)"
        ),
    )

    def __str__(self):
        return "{} ({})".format(self.name, self.camp.title)


def create_ticket_token(string):
    return hashlib.sha256(string).hexdigest()


def qr_code_base64(token):
    qr = qrcode.make(
        token, version=1, error_correction=qrcode.constants.ERROR_CORRECT_H
    ).resize((250, 250))
    file_like = io.BytesIO()
    qr.save(file_like, format="png")
    qrcode_base64 = base64.b64encode(file_like.getvalue())
    return qrcode_base64


class BaseTicket(CampRelatedModel, UUIDModel):
    ticket_type = models.ForeignKey("TicketType", on_delete=models.PROTECT)
    used = models.BooleanField(default=False)
    badge_handed_out = models.BooleanField(default=False)
    token = models.CharField(max_length=64, blank=True)
    badge_token = models.CharField(max_length=64, blank=True)

    class Meta:
        abstract = True

    camp_filter = "ticket_type__camp"

    @property
    def camp(self):
        return self.ticket_type.camp

    def save(self, **kwargs):
        self.token = self._get_token()
        self.badge_token = self._get_badge_token()
        super().save(**kwargs)

    def _get_token(self):
        return create_ticket_token(
            "{_id}{secret_key}".format(
                _id=self.uuid, secret_key=settings.SECRET_KEY
            ).encode("utf-8")
        )

    def _get_badge_token(self):
        return create_ticket_token(
            "{_id}{secret_key}-badge".format(
                _id=self.uuid, secret_key=settings.SECRET_KEY
            ).encode("utf-8")
        )

    def get_qr_code_url(self):
        return "data:image/png;base64,{}".format(
            qr_code_base64(self._get_token()).decode("utf-8")
        )

    def get_qr_badge_code_url(self):
        return "data:image/png;base64,{}".format(
            qr_code_base64(self._get_badge_token()).decode("utf-8")
        )

    def generate_pdf(self):
        formatdict = {"ticket": self}

        if self.ticket_type.single_ticket_per_product and self.shortname == "shop":
            formatdict["quantity"] = self.orp.quantity

        return generate_pdf_letter(
            filename="{}_ticket_{}.pdf".format(self.shortname, self.pk),
            formatdict=formatdict,
            template="pdf/ticket.html",
        )


class SponsorTicket(BaseTicket):
    sponsor = models.ForeignKey("sponsors.Sponsor", on_delete=models.PROTECT)

    def __str__(self):
        return "SponsorTicket: {}".format(self.pk)

    @property
    def shortname(self):
        return "sponsor"


class DiscountTicket(BaseTicket):
    price = models.IntegerField(
        help_text=_("Price of the discounted ticket (in DKK, including VAT).")
    )

    def __str__(self):
        return "DiscountTicket: {}".format(self.pk)

    @property
    def shortname(self):
        return "discount"


class ShopTicket(BaseTicket):
    order = models.ForeignKey(
        "shop.Order", related_name="shoptickets", on_delete=models.PROTECT
    )
    product = models.ForeignKey("shop.Product", on_delete=models.PROTECT)

    name = models.CharField(
        max_length=100,
        help_text=(
            "Name of the person this ticket belongs to. "
            "This can be different from the buying user."
        ),
        null=True,
        blank=True,
    )

    email = models.EmailField(null=True, blank=True)

    # overwrite the _get_token method because old tickets use the user_id
    def _get_token(self):
        return hashlib.sha256(
            "{_id}{user_id}{secret_key}".format(
                _id=self.pk, user_id=self.order.user.pk, secret_key=settings.SECRET_KEY
            ).encode("utf-8")
        ).hexdigest()

    def __str__(self):
        return "Ticket {user} {product}".format(
            user=self.order.user, product=self.product
        )

    def get_absolute_url(self):
        return str(reverse_lazy("tickets:shopticket_edit", kwargs={"pk": self.pk}))

    @property
    def shortname(self):
        return "shop"

    @property
    def orp(self):
        return OrderProductRelation.objects.get(product=self.product, order=self.order)
