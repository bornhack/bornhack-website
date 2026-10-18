"""Custom managers and querysets for the Camp model."""

from __future__ import annotations

from typing import Self

from django.contrib.auth.models import User
from django.db import models
from django.db.models import ExpressionWrapper
from django.db.models import F
from django.db.models import Func
from django.db.models import OuterRef
from django.db.models import Subquery
from django.db.models.functions import Coalesce


class NASum(models.Sum):
    contains_aggregate = False


class NACount(models.Count):
    contains_aggregate = False


class CampQuerySet(models.QuerySet):
    """Custom qs for the Camp model."""

    def annotate_volunteer_count(self) -> Self:
        """Annotate the number of volunteers across all teams."""
        return self.annotate(
            volunteer_count=models.Subquery(
                User.objects.filter(
                    teammember__approved=True,
                    teammember__team__camp=models.OuterRef("pk"),
                )
                .distinct()
                .annotate(
                    c=NACount("pk", distinct=True),
                )
                .values("c"),
            ),
        )

    def annotate_participants(self, checked_in: bool = True) -> Self:
        """Annotate the number of checked-in human participants."""
        from tickets.models import PrizeTicket
        from tickets.models import ShopTicket
        from tickets.models import SponsorTicket

        shop_subq = Subquery(
            ShopTicket.objects.filter(
                used_at__isnull=not checked_in,
                ticket_type__human_access=True,
                ticket_type__camp=OuterRef("pk"),
            )
            .order_by()
            .annotate(
                c=ExpressionWrapper(Func(F("uuid"), function="COUNT"), output_field=models.IntegerField()),
            )
            .values("c"),
        )

        sponsor_subq = Subquery(
            SponsorTicket.objects.filter(
                used_at__isnull=not checked_in,
                ticket_type__human_access=True,
                ticket_type__camp=OuterRef("pk"),
            )
            .order_by()
            .annotate(
                c=ExpressionWrapper(Func(F("uuid"), function="COUNT"), output_field=models.IntegerField()),
            )
            .values("c"),
        )

        prize_subq = Subquery(
            PrizeTicket.objects.filter(
                used_at__isnull=not checked_in,
                ticket_type__human_access=True,
                ticket_type__camp=OuterRef("pk"),
            )
            .order_by()
            .annotate(
                c=ExpressionWrapper(Func(F("uuid"), function="COUNT"), output_field=models.IntegerField()),
            )
            .values("c"),
        )

        used = "used" if checked_in else "unused"
        keys = {
            "shop": f"shop_tickets_{used}",
            "sponsor": f"sponsor_tickets_{used}",
            "prize": f"prize_tickets_{used}",
            "total": f"total_tickets_{used}",
        }
        kwargs = {
            keys["shop"]: shop_subq,
            keys["sponsor"]: sponsor_subq,
            keys["prize"]: prize_subq,
            keys["total"]: Coalesce(F(keys["shop"]), 0)
            + Coalesce(F(keys["sponsor"]), 0)
            + Coalesce(F(keys["prize"]), 0),
        }
        return self.annotate(**kwargs)

    def annotate_pos_data(self) -> Self:
        """Annotate PoS sales data."""
        from economy.models import PosSale

        bar_subq = Subquery(
            PosSale.objects.filter(
                transaction__pos__name="Bar",
                transaction__pos__team__camp=OuterRef("pk"),
            )
            .order_by()
            .annotate(
                sales_sum=NASum("sales_price"),
            )
            .annotate(total=Coalesce(NASum("sales_price"), 0))
            .values("total"),
        )

        info_subq = Subquery(
            PosSale.objects.filter(
                transaction__pos__name="Infodesk",
                transaction__pos__team__camp=OuterRef("pk"),
            )
            .order_by()
            .annotate(
                sales_sum=NASum("sales_price"),
            )
            .annotate(total=Coalesce(NASum("sales_price"), 0))
            .values("total"),
        )

        alco_subq = Subquery(
            PosSale.objects.filter(
                product__abv__gt=0,
                transaction__pos__team__camp=OuterRef("pk"),
            )
            .order_by()
            .annotate(
                sales_sum=NASum("sales_price"),
            )
            .annotate(total=Coalesce(NASum("sales_price"), 0))
            .values("total"),
        )

        nonalco_subq = Subquery(
            PosSale.objects.filter(
                product__abv=0,
                transaction__pos__team__camp=OuterRef("pk"),
            )
            .order_by()
            .annotate(
                sales_sum=NASum("sales_price"),
            )
            .annotate(total=Coalesce(NASum("sales_price"), 0))
            .values("total"),
        )

        total_subq = Subquery(
            PosSale.objects.filter(
                transaction__pos__team__camp=OuterRef("pk"),
            )
            .order_by()
            .annotate(
                sales_sum=NASum("sales_price"),
            )
            .annotate(total=Coalesce(NASum("sales_price"), 0))
            .values("total"),
        )

        return self.annotate(
            sales_sum_alc=alco_subq,
            sales_sum_nonalc=nonalco_subq,
            sales_sum_bar=bar_subq,
            sales_sum_info=info_subq,
            sales_sum_total=total_subq,
        )
