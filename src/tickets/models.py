from __future__ import annotations

import base64
import hashlib
import io
import logging
from typing import Union

import qrcode
from django.conf import settings
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel
from utils.models import CreatedUpdatedModel
from utils.models import UUIDModel
from utils.pdf import generate_pdf_letter

from .managers import PrizeTicketQuerySet
from .managers import ShopTicketManager
from .managers import ShopTicketQuerySet
from .managers import SponsorTicketQuerySet
from .managers import TicketGroupQuerySet
from .managers import TicketTypeQuerySet

logger = logging.getLogger(f"bornhack.{__name__}")


class TicketType(
    ExportModelOperationsMixin("ticket_type"),
    CampRelatedModel,
    UUIDModel,
):
    """TicketType can be full week, one day, cabins, parking,
    merch, hax, massage, etc.
    """

    objects = TicketTypeQuerySet.as_manager()
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
    human_access = models.BooleanField(
        default=False,
        help_text="True for ticket types which grant humans access to the event",
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.camp.title})"


def create_ticket_token(string):
    return hashlib.sha256(string).hexdigest()


def qr_code_base64(token):
    qr = qrcode.make(
        token,
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
    ).resize((250, 250))
    file_like = io.BytesIO()
    qr.save(file_like, format="png")
    return base64.b64encode(file_like.getvalue())


class BaseTicket(CampRelatedModel, UUIDModel):
    ticket_type = models.ForeignKey("TicketType", on_delete=models.PROTECT)
    used_at = models.DateTimeField(null=True, blank=True)
    used_pos = models.ForeignKey(
        "economy.Pos",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name=None,
        help_text="The Pos this ticket was scanned in",
    )
    used_pos_user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name=None,
        help_text="The PoS user who scanned this ticket",
    )

    badge_handed_out = models.BooleanField(default=False)
    token = models.CharField(max_length=64, blank=True)
    badge_token = models.CharField(max_length=64, blank=True)

    class Meta:
        abstract = True
        ordering = ["-created"]

    camp_filter = "ticket_type__camp"

    @property
    def camp(self):
        return self.ticket_type.camp

    def save(self, **kwargs) -> None:
        self.token = self._get_token()
        self.badge_token = self._get_badge_token()
        super().save(**kwargs)

    def _get_token(self):
        return create_ticket_token(
            f"{self.uuid}{settings.SECRET_KEY}".encode(),
        )

    def _get_badge_token(self):
        return create_ticket_token(
            f"{self.uuid}{settings.SECRET_KEY}-badge".encode(),
        )

    def get_qr_code_url(self):
        return "data:image/png;base64,{}".format(
            qr_code_base64(self._get_token()).decode("utf-8"),
        )

    def get_qr_badge_code_url(self):
        return "data:image/png;base64,{}".format(
            qr_code_base64(self._get_badge_token()).decode("utf-8"),
        )

    def get_pdf_formatdict(self):
        return {"ticket": self}

    def generate_pdf(self):
        return generate_pdf_letter(
            filename=f"{self.shortname}_ticket_{self.pk}.pdf",
            formatdict=self.get_pdf_formatdict(),
            template="pdf/ticket.html",
        )

    def mark_as_used(self, *, pos, user) -> None:
        self.used_at = timezone.now()
        self.used_pos = pos
        self.used_pos_user = user
        self.save()


class SponsorTicket(ExportModelOperationsMixin("sponsor_ticket"), BaseTicket):
    """Sponsor tickets live here with an FK to the sponsor."""

    objects = SponsorTicketQuerySet.as_manager()
    sponsor = models.ForeignKey("sponsors.Sponsor", on_delete=models.PROTECT)

    def __str__(self) -> str:
        return f"SponsorTicket: {self.pk}"

    @property
    def shortname(self) -> str:
        return "sponsor"


class PrizeTicket(ExportModelOperationsMixin("prize_ticket"), BaseTicket):
    """Prize tickets for winners of CTF etc with an FK to the user."""

    objects = PrizeTicketQuerySet.as_manager()
    user = models.ForeignKey(
        "auth.User",
        related_name="prize_tickets",
        on_delete=models.PROTECT,
        help_text="The user to whom this PrizeTicket belongs.",
    )

    comment = models.TextField(help_text="A comment about this PrizeTicket (what was it given for)")

    @property
    def shortname(self) -> str:
        return "prize"


class TicketGroup(
    ExportModelOperationsMixin("ticket_group"),
    CreatedUpdatedModel,
    UUIDModel,
):
    objects = TicketGroupQuerySet.as_manager()

    opr = models.ForeignKey(
        "shop.OrderProductRelation",
        related_name="ticketgroups",
        on_delete=models.PROTECT,
    )


class ShopTicket(ExportModelOperationsMixin("shop_ticket"), BaseTicket):
    objects = ShopTicketManager.from_queryset(ShopTicketQuerySet)()

    opr = models.ForeignKey(
        "shop.OrderProductRelation",
        related_name="shoptickets",
        on_delete=models.PROTECT,
    )

    product = models.ForeignKey("shop.Product", on_delete=models.PROTECT)

    bundle_product = models.ForeignKey(
        "shop.Product",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )

    ticket_group = models.ForeignKey(
        "tickets.TicketGroup",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tickets",
    )

    name = models.CharField(
        max_length=100,
        help_text=("Name of the person this ticket belongs to. This can be different from the buying user."),
        null=True,
        blank=True,
    )

    # overwrite the _get_token method because old tickets use the user_id
    def _get_token(self):
        return hashlib.sha256(
            f"{self.pk}{self.order.user.pk}{settings.SECRET_KEY}".encode(),
        ).hexdigest()

    def __str__(self) -> str:
        return f"Ticket {self.pk} {self.product}"

    def get_absolute_url(self):
        return str(reverse_lazy("tickets:shopticket_edit", kwargs={"pk": self.pk}))

    @property
    def shortname(self) -> str:
        return "shop"

    @property
    def order(self):
        return self.opr.order

    def get_pdf_formatdict(self):
        formatdict = super().get_pdf_formatdict()
        if self.ticket_type.single_ticket_per_product and hasattr(self, "quantity"):
            formatdict["quantity"] = self.quantity
        return formatdict


TicketTypeUnion = Union[ShopTicket, SponsorTicket, PrizeTicket]
