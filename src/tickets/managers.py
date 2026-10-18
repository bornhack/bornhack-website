"""Custom managers and querysets."""

from __future__ import annotations

from typing import Self

from django.db import models
from django.db.models import Avg
from django.db.models import Count
from django.db.models import Exists
from django.db.models import F
from django.db.models import Q
from django.db.models import Subquery
from django.db.models import Sum
from django.db.models.functions import Coalesce


class ShopTicketManager(models.Manager):
    """Custom manager for ShopTicket."""

    def get_queryset(self):
        """Always annotage ticket quantity."""
        return super().get_queryset().annotate_quantity()


class BaseTicketQuerySet(models.QuerySet):
    """Base custom qs for Ticket Models."""

    def checked_in_count(self, human_only: bool = False) -> Self:
        """Aggregate and return the number of checked in tickets."""
        kwargs = {"used_at__isnull": False}
        if human_only:
            kwargs["ticket_type__human_access"] = True
        sts = self.filter(**kwargs).values("ticket_type__name").annotate(models.Count("pk"))
        return {st["ticket_type__name"]: st["pk__count"] for st in sts}


class ShopTicketQuerySet(BaseTicketQuerySet):
    """Custom qs for ShopTicket."""

    def annotate_quantity(self) -> Self:
        """Annotate quantity of tickets on each ticket.

        If the ticket is a bundle ticket, the quantity is the number
        of tickets in the bundle.

        If the ticket is not a bundle ticket, the quantity is the
        quantity of the order product relation.
        """
        from shop.models import SubProductRelation

        sub_product_relation_sub_query = models.Subquery(
            SubProductRelation.objects.filter(
                bundle_product=models.OuterRef("bundle_product"),
                sub_product=models.OuterRef("product"),
            ).values("number_of_tickets")[:1],
        )
        return self.annotate(
            quantity=models.Case(
                models.When(
                    bundle_product__isnull=True,
                    then=models.F("opr__quantity"),
                ),
                models.When(
                    bundle_product__isnull=False,
                    then=sub_product_relation_sub_query,
                ),
                default=models.Value(1),
            ),
        )


class SponsorTicketQuerySet(BaseTicketQuerySet):
    """Custom qs for SponsorTicket."""


class PrizeTicketQuerySet(BaseTicketQuerySet):
    """Custom qs for PrizeTicket."""


class TicketGroupQuerySet(models.QuerySet):
    """Custom qs for TicketGroup"""

    def annotate_ticket_info(self):
        from .models import ShopTicket

        used_tickets_subquery = ShopTicket.objects.filter(
            ticket_group=models.OuterRef("pk"),
            used_at__isnull=False,
        )
        tickets_subquery = ShopTicket.objects.filter(ticket_group=models.OuterRef("pk"))
        return self.annotate(
            has_used_tickets=Exists(used_tickets_subquery),
            has_tickets=Exists(tickets_subquery),
        ).distinct("uuid", "created")


class TicketTypeQuerySet(models.QuerySet):
    """Custom qs for TicketType."""

    def with_price_stats(self):
        """We have to make subqueries to be able to annotate the specific
        ticket type. Otherwise, values would be accumulative across all types.
        """
        from .models import TicketType

        quantity = F("product__orderproductrelation__quantity") - Coalesce(
            "product__orderproductrelation__rprs__quantity",
            0,
        )

        subquery_base = TicketType.objects.filter(pk=models.OuterRef("pk")).annotate(
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
            TicketType.objects.filter(pk=models.OuterRef("pk"))
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
