"""Custom managers and querysets for the Camp model."""

from __future__ import annotations

from typing import Self

from django.db import models
from django.db.models import ExpressionWrapper
from django.db.models import F
from django.db.models import Func
from django.db.models import OuterRef
from django.db.models import Subquery
from django.db.models.functions import Coalesce


class CampQuerySet(models.QuerySet):
    """Custom qs for the Camp model."""

    def annotate_volunteer_count(self) -> Self:
        """Annotate the number of volunteers across all teams."""
        from teams.models import TeamMember

        return self.annotate(
            volunteer_count=Subquery(
                TeamMember.objects.order_by()
                .filter(team__camp=OuterRef("pk"))
                .annotate(
                    c=models.Func("pk", function="COUNT"),
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
        from economy.models import PosProduct

        alco_subq = Subquery(
            PosProduct.objects.annotate_sales(
                camp=OuterRef("pk"),
            )
            .filter(
                abv__gt=0,
                sales_sum__gt=0,
            )
            .annotate(total=models.Func("sales_sum", function="SUM"))
            .values("total"),
        )
        nonalco_subq = Subquery(
            PosProduct.objects.annotate_sales(
                camp=OuterRef("pk"),
            )
            .filter(
                abv=0,
                sales_sum__gt=0,
            )
            .annotate(total=models.Func("sales_sum", function="SUM"))
            .values("total"),
        )

        return self.annotate(
            sales_sum_alc=alco_subq,
            sales_sum_nonalc=nonalco_subq,
        )
