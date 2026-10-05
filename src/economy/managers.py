"""Custom managers and querysets."""
from django.urls import reverse
from django.db import models
from typing import Self
from django.http import QueryDict
from django.contrib.postgres.fields.ranges import RangeStartsWith
from datetime import timedelta
from utils.querystring import querystring_from_request

class PosSaleQuerySet(models.QuerySet):
    """Custom qs for PosSale."""

    def annotate_pos_date(self) -> Self:
        """Annotate the PoS report start date."""
        return self.annotate(
            # get just the date
            pos_date=models.functions.TruncDate(
                # get the date of the start of the PosReport period
                RangeStartsWith("transaction__pos_report__period")
            ),
        )

    def annotate_cost_profit(self) -> Self:
        """Annotate the latest cost and calculated profit for sale."""
        # define subq for getting latest product cost
        from .models import PosProductCost
        latest_cost = PosProductCost.objects.filter(
            product__uuid=models.OuterRef("product__uuid"),
            camp=models.OuterRef("transaction__pos__team__camp"),
        ).order_by("-timestamp")
        return self.annotate(
            cost=models.functions.Coalesce(
                models.Subquery(latest_cost.values("product_cost")[:1]),
                0,
                output_field=models.DecimalField(),
            ),
            # make profit 0 if cost is 0
            profit=models.Case(
                models.When(cost=0, then=models.Value(0)),
                default=models.Sum(models.F("sales_price") - models.F("cost")),
                # throw away decimals for profit calculation
                output_field=models.IntegerField(),
            ),
        )

    def get_daily_sales_by_date_treemap(self, aggregator: models.aggregates.Sum|models.aggregates.Count, request) -> dict[str, dict[str, list[str]]]:
        """Return apexcharts ready data for PosSale grouped by date.

        aggregator can be Sum or Count.

        Date is the BornHack definition meaning transactions after midnight
        belong to the day the PosReport started (usually the day before).
        """
        by_date = {}
        qs = self.annotate_pos_date().values(
            "pos_date", "product__tags", "transaction__pos_report__pos__team__camp__slug", "transaction__pos_report__period"
        ).annotate(
            # either count or sum all the sales
            total_sales=aggregator("sales_price"),
        ).order_by("pos_date")
        url = reverse(
            "backoffice:possale_list_table",
            kwargs={"camp_slug": request.camp.slug},
        )
        for day in qs:
            if day["product__tags"] == "":
                # skip untagged for now
                continue
            date = day["pos_date"]
            # has this date been seen before?
            if date not in by_date:
                by_date[date] = []
            # create querydict for the link for this data
            qs = querystring_from_request(request=request, **{
                "tags": day["product__tags"],
                "pos_date_after": day["pos_date"],
                "pos_date_before": day["pos_date"],
            })
            # append this tag and salecount to the list for this date
            by_date[date].append({
                "x": day["product__tags"],
                "y": day["total_sales"],
                # add a url with date and tags query filter
                "url": f"{url}{qs}",
            })
        return {
            "series": [{"name": k, "data": v} for k, v in by_date.items()],
            "labels": list(by_date.keys()),
        }

    def get_daily_sales_by_date(self, aggregator: models.aggregates.Sum|models.aggregates.Count, field: str, request) -> dict[str, list[str]]:
        # get unique tags and dates for this qs
        tags = sorted(list(set(self.values_list("product__tags", flat=True))))
        dates = sorted(list(set(self.annotate_pos_date().values("pos_date").values_list("pos_date", flat=True))))
        by_tag = {}
        url = reverse(
            "backoffice:possale_list_table",
            kwargs={"camp_slug": request.camp.slug},
        )
        for tag in tags:
            aggs = {
                str(date): aggregator(
                    field,
                    filter=models.Q(product__tags=tag, pos_date=date)
                ) for date in dates}
            qs = sorted(self.annotate_pos_date().aggregate(**aggs).items())
            urls = []
            for date, sales in qs:
                query = querystring_from_request(request=request, **{
                    "tags": tag,
                    "pos_date_after": date,
                    "pos_date_before": date,
                })
                urls.append(f"{url}{query}")
            # a list of values in the right order
            by_tag[tag] = {
                "name": tag,
                "data": [sales for date, sales in qs],
                "urls": urls,
            }
        return {
            "series": [v for v in by_tag.values()],
            "labels": dates,
        }

    def get_daily_sales_by_tags(self, aggregator: models.aggregates.Sum|models.aggregates.Count, field: str, request) -> dict[str, list[str]]:
        # get unique tags and dates for this qs
        tags = sorted(list(set(self.values_list("product__tags", flat=True))))
        dates = sorted(list(set(self.annotate_pos_date().values("pos_date").values_list("pos_date", flat=True))))
        by_date = {}
        url = reverse(
            "backoffice:possale_list_table",
            kwargs={"camp_slug": request.camp.slug},
        )
        for date in dates:
            aggs = {
                tag: aggregator(
                    field,
                    filter=models.Q(product__tags=tag, pos_date=date)
                ) for tag in tags}
            qs = sorted(self.annotate_pos_date().aggregate(**aggs).items())
            urls = []
            for tag, sales in qs:
                query = querystring_from_request(request=request, **{
                    "tags": tag,
                    "pos_date_after": date,
                    "pos_date_before": date,
                })
                urls.append(f"{url}{query}")
            by_date[date] = {
                "name": date,
                "data": [sales for tag, sales in qs],
                "urls": urls,
            }
        return {
            "series": [v for v in by_date.values()],
            "labels": tags,
        }


class PosTransactionQuerySet(models.QuerySet):
    """Custom qs for PosTransaction."""

    def annotate_pos_date(self) -> Self:
        """Annotate the PoS report start date."""
        return self.annotate(
            # get just the date
            pos_date=models.functions.TruncDate(
                # get the date of the start of the PosReport period
                RangeStartsWith("pos_report__period")
            ),
        )
