import base64
import hashlib
import io
import logging
from decimal import Decimal
from typing import Union

import qrcode
from django.conf import settings
from django.db import models
from django.db.models import Count
from django.db.models import Expression
from django.db.models import ExpressionWrapper
from django.db.models import F
from django.db.models import OuterRef
from django.db.models import Subquery
from django.db.models import Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel
from utils.models import UUIDModel
from utils.pdf import generate_pdf_letter

logger = logging.getLogger("bornhack.%s" % __name__)


class TicketTypeQuerySet(models.QuerySet):
    def with_price_stats(self):
        def _make_subquery(annotation: Union[Expression, F]) -> Subquery:
            return Subquery(
                TicketType.objects.annotate(annotation_value=annotation)
                .filter(pk=OuterRef("pk"))
                .values("annotation_value")[:1],
            )

        quantity = F("product__orderproductrelation__quantity")
        cost = quantity * F("product__cost")
        income = quantity * F("product__price")

        avg_ticket_price = Subquery(
            TicketType.objects.annotate(units=Sum(quantity))
            .annotate(income=Sum(income))
            .annotate(
                avg_ticket_price=ExpressionWrapper(
                    F("income") * Decimal("1.0") / F("units"),
                    output_field=models.DecimalField(),
                ),
            )
            .filter(pk=OuterRef("pk"))
            .values("avg_ticket_price")[:1],
            output_field=models.DecimalField(),
        )

        return self.annotate(
            shopticket_count=_make_subquery(Count("shopticket")),
            total_units_sold=_make_subquery(quantity),
            total_income=_make_subquery(income),
            total_cost=_make_subquery(cost),
            total_profit=_make_subquery(income - cost),
            avg_ticket_price=avg_ticket_price,
        ).distinct()


# TicketType can be full week, one day, cabins, parking, merch, hax, massage, etc.
class TicketType(
    ExportModelOperationsMixin("ticket_type"),
    CampRelatedModel,
    UUIDModel,
):
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

    def __str__(self):
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
    qrcode_base64 = base64.b64encode(file_like.getvalue())
    return qrcode_base64


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
                _id=self.uuid,
                secret_key=settings.SECRET_KEY,
            ).encode("utf-8"),
        )

    def _get_badge_token(self):
        return create_ticket_token(
            "{_id}{secret_key}-badge".format(
                _id=self.uuid,
                secret_key=settings.SECRET_KEY,
            ).encode("utf-8"),
        )

    def get_qr_code_url(self):
        return "data:image/png;base64,{}".format(
            qr_code_base64(self._get_token()).decode("utf-8"),
        )

    def get_qr_badge_code_url(self):
        return "data:image/png;base64,{}".format(
            qr_code_base64(self._get_badge_token()).decode("utf-8"),
        )

    def generate_pdf(self):
        formatdict = {"ticket": self}

        if self.ticket_type.single_ticket_per_product and self.shortname == "shop":
            formatdict["quantity"] = self.opr.quantity

        return generate_pdf_letter(
            filename=f"{self.shortname}_ticket_{self.pk}.pdf",
            formatdict=formatdict,
            template="pdf/ticket.html",
        )

    def mark_as_used(self, *, pos, user):
        self.used_at = timezone.now()
        self.used_pos = pos
        self.used_pos_user = user
        self.save()


class SponsorTicket(ExportModelOperationsMixin("sponsor_ticket"), BaseTicket):
    sponsor = models.ForeignKey("sponsors.Sponsor", on_delete=models.PROTECT)

    def __str__(self):
        return f"SponsorTicket: {self.pk}"

    @property
    def shortname(self):
        return "sponsor"


class DiscountTicket(ExportModelOperationsMixin("discount_ticket"), BaseTicket):
    price = models.IntegerField(
        help_text=_("Price of the discounted ticket (in DKK, including VAT)."),
    )

    def __str__(self):
        return f"DiscountTicket: {self.pk}"

    @property
    def shortname(self):
        return "discount"


class ShopTicket(ExportModelOperationsMixin("shop_ticket"), BaseTicket):
    opr = models.ForeignKey(
        "shop.OrderProductRelation",
        related_name="shoptickets",
        on_delete=models.PROTECT,
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
                _id=self.pk,
                user_id=self.order.user.pk,
                secret_key=settings.SECRET_KEY,
            ).encode("utf-8"),
        ).hexdigest()

    def __str__(self):
        return "Ticket {user} {product}".format(
            user=self.order.user,
            product=self.product,
        )

    def get_absolute_url(self):
        return str(reverse_lazy("tickets:shopticket_edit", kwargs={"pk": self.pk}))

    @property
    def shortname(self):
        return "shop"

    @property
    def order(self):
        return self.opr.order


TicketTypeUnion = Union[ShopTicket, SponsorTicket, DiscountTicket]
