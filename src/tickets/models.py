from __future__ import annotations

import base64
import hashlib
import io
import logging
from typing import Union

import qrcode
from django.conf import settings
from django.db import models
from django.db.models import Avg
from django.db.models import Case
from django.db.models import Count
from django.db.models import Exists
from django.db.models import Expression
from django.db.models import F
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import QuerySet
from django.db.models import Subquery
from django.db.models import Sum
from django.db.models import Value
from django.db.models import When
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel
from utils.models import CreatedUpdatedModel
from utils.models import UUIDModel
from utils.pdf import generate_pdf_letter

logger = logging.getLogger(f"bornhack.{__name__}")


class TicketTypeQuerySet(models.QuerySet):
    def with_price_stats(self):
        # We have to make subqueries to be able to annotate the specific
        # ticket type. Otherwise, values would be accumulative across all types.
        def _make_subquery(annotation: Expression | F) -> Subquery:
            return Subquery(
                TicketType.objects.annotate(annotation_value=annotation)
                .filter(pk=OuterRef("pk"))
                .values("annotation_value")[:1],
            )

        quantity = F("product__orderproductrelation__quantity") - Coalesce(
            "product__orderproductrelation__rprs__quantity",
            0,
        )

        subquery_base = TicketType.objects.filter(pk=OuterRef("pk")).annotate(
            total_units_sold=Sum(
                quantity,
                filter=Q(product__orderproductrelation__order__paid=True),
            ),
            total_cost=Sum(
                F("product__cost") * quantity,
                filter=Q(product__orderproductrelation__order__paid=True),
            ),
            total_income=Sum(
                F("product__price") * quantity,
                filter=Q(product__orderproductrelation__order__paid=True),
            ),
            avg_ticket_price=Avg("product__price"),
        )

        total_units_sold = subquery_base.values("total_units_sold")
        cost_per_product = subquery_base.values("total_cost")
        income_per_product = subquery_base.values("total_income")
        avg_ticket_price = subquery_base.values("avg_ticket_price")

        # Shop ticket count has to be its own queryset since the count messes up the other subqueries.
        shop_ticket_count = (
            TicketType.objects.filter(pk=OuterRef("pk"))
            .annotate(
                shop_ticket_count=Count("shopticket"),
            )
            .values("shop_ticket_count")
        )

        return self.annotate(
            total_units_sold=Subquery(total_units_sold),
            total_income=Subquery(income_per_product),
            total_cost=Subquery(cost_per_product),
            total_profit=Subquery(income_per_product) - Subquery(cost_per_product),
            avg_ticket_price=Subquery(avg_ticket_price),
            shopticket_count=Subquery(shop_ticket_count),
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
    sponsor = models.ForeignKey("sponsors.Sponsor", on_delete=models.PROTECT)

    def __str__(self) -> str:
        return f"SponsorTicket: {self.pk}"

    @property
    def shortname(self) -> str:
        return "sponsor"


class DiscountTicket(ExportModelOperationsMixin("discount_ticket"), BaseTicket):
    price = models.IntegerField(
        help_text=_("Price of the discounted ticket (in DKK, including VAT)."),
    )

    def __str__(self) -> str:
        return f"DiscountTicket: {self.pk}"

    @property
    def shortname(self) -> str:
        return "discount"


class TicketGroup(
    ExportModelOperationsMixin("ticket_group"),
    CreatedUpdatedModel,
    UUIDModel,
):
    class QuerySet(QuerySet):
        def annotate_ticket_info(self):
            used_tickets_subquery = ShopTicket.objects.filter(
                ticket_group=OuterRef("pk"),
                used_at__isnull=False,
            )
            tickets = ShopTicket.objects.filter(ticket_group=OuterRef("pk"))
            return self.annotate(
                has_used_tickets=Exists(used_tickets_subquery),
                has_tickets=Exists(tickets),
            ).distinct("uuid")

    objects = QuerySet.as_manager()

    opr = models.ForeignKey(
        "shop.OrderProductRelation",
        related_name="ticketgroups",
        on_delete=models.PROTECT,
    )


class ShopTicket(ExportModelOperationsMixin("shop_ticket"), BaseTicket):
    class Manager(models.Manager):
        def get_queryset(self):
            """Return a queryset which has quantity of annotated on each ticket.

            If the ticket is a bundle ticket, the quantity is the number of tickets in the bundle.
            If the ticket is not a bundle ticket, the quantity is the quantity of the order product relation.
            """
            from shop.models import SubProductRelation

            sub_product_relation_sub_query = Subquery(
                SubProductRelation.objects.filter(
                    bundle_product=OuterRef("bundle_product"),
                    sub_product=OuterRef("product"),
                ).values("number_of_tickets")[:1],
            )
            return (
                super()
                .get_queryset()
                .annotate(
                    quantity=Case(
                        When(
                            bundle_product__isnull=True,
                            then=F("opr__quantity"),
                        ),
                        When(
                            bundle_product__isnull=False,
                            then=sub_product_relation_sub_query,
                        ),
                        default=Value(1),
                    ),
                )
            )

    objects = Manager()

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

    email = models.EmailField(null=True, blank=True)

    # overwrite the _get_token method because old tickets use the user_id
    def _get_token(self):
        return hashlib.sha256(
            f"{self.pk}{self.order.user.pk}{settings.SECRET_KEY}".encode(),
        ).hexdigest()

    def __str__(self) -> str:
        return f"Ticket {self.order.user} {self.product}"

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


TicketTypeUnion = Union[ShopTicket, SponsorTicket, DiscountTicket]
