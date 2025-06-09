from __future__ import annotations

import django_tables2 as tables
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import localize
from django.utils.safestring import mark_safe

from economy.models import PosProduct
from economy.models import PosProductCost
from economy.models import PosSale
from economy.models import PosTransaction
from utils.querystring import querystring_from_request


def filter_button(text, request, **kwargs):
    """Add a filter button before the provided text with a querystring updated with the provided kwargs."""
    querystring = querystring_from_request(request, **kwargs)
    button = f'<a href="{request.path}{querystring}"><i class="fas fa-filter"></i></a>'
    return mark_safe(f"{button}&nbsp;{text}")


def filter_link(text, request, **kwargs):
    """Wrap the provided text in a link with a querystring updated with the provided kwargs."""
    querystring = querystring_from_request(request, **kwargs)
    return mark_safe(f'<a href="{request.path}{querystring}">{text}</a>')


def intround(value):
    """Remove decimals if they are all 0."""
    if value == int(value):
        return int(value)
    return round(value, 2)


# ############ COLUMNS #################


class TagsColumn(tables.Column):
    def render(self, value, table):
        output = []
        for tag in value.split(","):
            output.append(
                filter_link(
                    f'<span class="badge">{tag}</span>',
                    table.request,
                    tags=tag,
                ),
            )
        return mark_safe("&nbsp;".join(output))


class HaxColumn(tables.Column):
    def render(self, value, table):
        return filter_button(
            f"{value} HAX",
            table.request,
            price_min=value,
            price_max=value,
        )


class PosColumn(tables.Column):
    def render(self, value, table):
        return filter_button(value, table.request, pos=value)


class TimestampColumn(tables.Column):
    def render(self, value, table):
        return filter_button(
            localize(timezone.localtime(value), use_l10n=True),
            table.request,
            timestamp_after=value,
            timestamp_before=value,
        )


class SizeColumn(tables.Column):
    def render(self, value, record, table):
        value = intround(value)
        unit = record.product.size_unit if hasattr(record, "product") else record.size_unit
        return filter_button(
            f"{value} {unit}",
            table.request,
            size_min=value,
            size_max=value,
            unit=unit,
        )


class BrandColumn(tables.Column):
    def render(self, value, table):
        return filter_button(value, table.request, brand=value)


class NameColumn(tables.Column):
    def render(self, value, record, table):
        button = filter_button(value, table.request, name=value)
        url = reverse(
            "backoffice:posproduct_list",
            kwargs={"camp_slug": table.request.camp.slug},
        )
        product = record.product if hasattr(record, "product") else record
        link = f'<a href="{url}?prodid={product.external_id}">(show)</a>'
        return mark_safe(f"{button} {link}")


class DescriptionColumn(tables.Column):
    def render(self, value, table):
        return filter_button(value, table.request, description=value)


class CostColumn(tables.Column):
    def render(self, value, table):
        return filter_button(
            f"{value} DKK",
            table.request,
            cost_min=value,
            cost_max=value,
        )


# ############ TABLES #################


class PosProductTable(tables.Table):
    """Table with PosProduct objects."""

    brand_name = BrandColumn(verbose_name="Brand")
    name = NameColumn(verbose_name="Name")
    description = DescriptionColumn(verbose_name="Description")
    sales_price = HaxColumn(verbose_name="Price")
    cost = tables.Column(verbose_name="Cost", empty_values=())
    tags = TagsColumn()
    unit_size = SizeColumn()
    expenses = tables.Column(verbose_name="Expenses")
    update = tables.TemplateColumn(
        verbose_name="Update",
        template_code='<a href="{{ record.uuid }}/update/" class="btn btn-primary"><i class="fas fa-edit"></i></a>',
        orderable=False,
    )

    def __init__(self, data, *args, **kwargs) -> None:
        """Do select/prefetch_related here so it happens after django-tables2s pagination."""
        super().__init__(
            data.prefetch_related(
                "expenses__camp",
                "pos_product_costs",
            ),
            *args,
            **kwargs,
        )

    def render_sales_price(self, value):
        return filter_button(
            f"{value} HAX",
            self.request,
            price_min=value,
            price_max=value,
        )

    def render_abv(self, value):
        return filter_button(
            f"{intround(value)}%",
            self.request,
            abv_min=value,
            abv_max=value,
        )

    def render_sales_count(self, value, record):
        count = filter_button(
            value,
            self.request,
            sales_count_min=value,
            sales_count_max=value,
        )
        qs = querystring_from_request(self.request, prodid=record.external_id)
        url = reverse(
            "backoffice:possale_list",
            kwargs={"camp_slug": self.request.camp.slug},
        )
        link = f'<a href="{url}{qs}">show</a>'
        return mark_safe(f"{count} ({link})")

    def render_sales_sum(self, value, record):
        count = filter_button(
            value,
            self.request,
            sales_sum_min=value,
            sales_sum_max=value,
        )
        return mark_safe(f"{count}&nbsp;HAX")

    def render_expenses(self, value, record):
        if not record.expenses.exists():
            return "N/A"
        output = []
        count = 0
        for expense in record.expenses.all():
            url = expense.get_backoffice_url()
            output.append(f'<a href="{url}">#{count}</a>')
            count += 1
        return mark_safe(", ".join(output))

    def render_cost(self, value, record, table):
        if value == 0:
            return "N/A"
        cost_url = reverse(
            "backoffice:posproductcost_list",
            kwargs={"camp_slug": table.request.camp.slug},
        )
        costs_count_label = f"{record.cost_count} {'cost' if record.cost_count == 1 else 'costs'}"
        link = f'<a href="{cost_url}?prodid={record.external_id}">({costs_count_label})</a>'
        return mark_safe(f"{value} DKK<br>{link}<br>")

    def order_expenses(self, queryset, is_descending):
        queryset = queryset.annotate(
            expense_count=models.Count("expenses"),
        ).order_by(("-" if is_descending else "") + "expense_count")
        return (queryset, True)

    class Meta:
        model = PosProduct
        fields = [
            "brand_name",
            "name",
            "description",
            "sales_price",
            "cost",
            "expenses",
            "unit_size",
            "abv",
            "tags",
            "sales_count",
            "sales_sum",
        ]


class PosSaleTable(tables.Table):
    """Table with PosSale objects."""

    transaction__pos__name = PosColumn(verbose_name="Pos")
    transaction__external_transaction_id = tables.Column(verbose_name="Transaction")
    transaction__timestamp = TimestampColumn(verbose_name="Timestamp")
    product__brand_name = BrandColumn(verbose_name="Brand")
    product__name = NameColumn(verbose_name="Name")
    product__unit_size = SizeColumn(verbose_name="Size")
    product__description = DescriptionColumn(verbose_name="Description")
    sales_price = HaxColumn(verbose_name="Price")
    product__tags = TagsColumn(verbose_name="Tags")
    cost = CostColumn(verbose_name="Cost")

    def __init__(self, data, *args, **kwargs) -> None:
        """Do select/prefetch_related and annotations here so it happens after django-tables2s pagination."""
        super().__init__(
            data
            # get Pos and PosTransaction
            .select_related("transaction__pos")
            # get PosProduct
            .select_related("product"),
            *args,
            **kwargs,
        )

    def render_transaction__external_transaction_id(self, value):
        return filter_button(value, self.request, txid=value)

    def render_profit(self, value, record):
        if record.cost == 0:
            return "N/A"
        return filter_button(
            f"{value} DKK",
            self.request,
            profit_min=value,
            profit_max=value,
        )

    class Meta:
        """Specify the model and which fields to include in the table."""

        model = PosSale
        fields = [
            "transaction__pos__name",
            "transaction__external_transaction_id",
            "transaction__timestamp",
            "product__brand_name",
            "product__name",
            "product__description",
            "product__unit_size",
            "product__tags",
            "sales_price",
            "cost",
            "profit",
        ]


class PosTransactionTable(tables.Table):
    external_user_id = tables.Column(verbose_name="Seller")
    pos__name = PosColumn(verbose_name="Pos")
    total = HaxColumn(verbose_name="Transaction Total")
    products = tables.Column(verbose_name="Items Sold")
    timestamp = TimestampColumn(verbose_name="Transaction Timestamp")

    def __init__(self, data, *args, **kwargs) -> None:
        """Do select/prefetch_related here so it happens after django-tables2s pagination."""
        super().__init__(
            data
            # get the parent Pos object
            .select_related("pos")
            # get PosSales for each PosTransaction
            .prefetch_related("pos_sales"),
            *args,
            **kwargs,
        )

    class Meta:
        model = PosTransaction
        fields = [
            "pos__name",
            "external_user_id",
            "timestamp",
            "products",
            "total",
        ]

    def render_external_user_id(self, value):
        return filter_button(value, self.request, seller=value)

    def render_products(self, value, record):
        count = filter_button(
            value,
            self.request,
            products_min=value,
            products_max=value,
        )
        url = reverse(
            "backoffice:possale_list",
            kwargs={"camp_slug": self.request.camp.slug},
        )
        link = f'<a href="{url}?txid={record.external_transaction_id}">show</a>'
        return mark_safe(f"{count} ({link})")


class PosProductCostTable(tables.Table):
    """Table with PosProductCost objects."""

    product__brand_name = BrandColumn(verbose_name="Brand")
    product__name = NameColumn(verbose_name="Name")
    product__description = DescriptionColumn(verbose_name="Description")
    product_cost = CostColumn(verbose_name="Product Cost")
    timestamp = TimestampColumn(verbose_name="Start Time")
    update = tables.TemplateColumn(
        verbose_name="Update",
        template_code='<a href="{{ record.uuid }}/update/" class="btn btn-primary"><i class="fas fa-edit"></i></a>',
        orderable=False,
    )

    def __init__(self, data, *args, **kwargs) -> None:
        """Do select/prefetch_related here so it happens after django-tables2s pagination."""
        super().__init__(
            data.prefetch_related("product"),
            *args,
            **kwargs,
        )

    class Meta:
        model = PosProductCost
        fields = [
            "product__brand_name",
            "product__name",
            "product__description",
            "timestamp",
            "product_cost",
        ]
