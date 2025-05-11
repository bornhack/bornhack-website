from django.db import models
from django_filters import FilterSet
from django_filters import filters

from .models import Pos
from .models import PosProduct
from .models import PosProductCost
from .models import PosSale
from .models import PosTransaction


def get_size_unit_widget_data(request):
    """Size unit dropdown data."""
    return (
        PosProduct.objects.filter(
            pos_sales__transaction__pos__team__camp=request.camp,
            pos_sales__isnull=False,
        )
        .values_list("size_unit", flat=True)
        .distinct()
    )


class PosProductFilter(FilterSet):
    brand = filters.CharFilter(
        field_name="brand_name",
        label="Brand Name Contains",
        lookup_expr="icontains",
    )
    name = filters.CharFilter(label="Name Contains", lookup_expr="icontains")
    description = filters.CharFilter(
        label="Description Contains",
        lookup_expr="icontains",
    )
    prodid = filters.CharFilter(field_name="external_id", label="Product ID")
    price = filters.RangeFilter(field_name="sales_price", label="Price")
    size = filters.RangeFilter(field_name="unit_size", label="Size")
    unit = filters.ModelChoiceFilter(
        field_name="size_unit",
        queryset=get_size_unit_widget_data,
        to_field_name="size_unit",
    )
    abv = filters.RangeFilter(label="ABV %")
    tags = filters.CharFilter(label="Tags Contain", lookup_expr="icontains")
    sales_count = filters.RangeFilter(label="# of Sales")
    sales_sum = filters.RangeFilter(label="Sales Sum")
    cost = filters.RangeFilter(label="Product Cost")

    class Meta:
        model = PosProduct
        fields = {}

    @property
    def qs(self):
        """Only show products sold at least once during current camp. Add annotations here to make sure they are filterable."""
        # define a reusable camp filter
        campfilter = models.Q(pos_sales__transaction__pos__team__camp=self.request.camp)
        # define subq for getting latest product cost
        latest_cost = PosProductCost.objects.filter(
            product__uuid=models.OuterRef("uuid"),
            camp=self.request.camp,
        ).order_by("-timestamp")

        # define subq for getting number of costs for this product
        cost_count = (
            PosProductCost.objects.filter(
                product=models.OuterRef("pk"),
                camp=self.request.camp,
            )  # filter by product and camp
            .values("product")  # group by product to return only a single row
            .annotate(cost_count=models.Count("uuid"))  # count number of costs
            .values("cost_count")  # select the count
        )

        # annotate sales count, sales sum, and cost
        self.queryset = PosProduct.objects.filter(
            campfilter,
            pos_sales__isnull=False,
        ).annotate(
            sales_count=models.Count("pos_sales", filter=campfilter),
            sales_sum=models.Sum("pos_sales__sales_price", filter=campfilter),
            # default cost to 0 if we have no costs for this product
            cost=models.functions.Coalesce(
                models.Subquery(latest_cost.values("product_cost")[:1]),
                0,
                output_field=models.DecimalField(),
            ),
            cost_count=models.Subquery(cost_count),
        )
        return super().qs


def get_pos_widget_data(request):
    """Pos picker dropdown data."""
    return Pos.objects.filter(team__camp=request.camp).values_list("name", flat=True)


class PosTransactionFilter(FilterSet):
    """FilterSet for PosTransaction filtering."""

    pos = filters.ModelChoiceFilter(
        field_name="pos__name",
        queryset=get_pos_widget_data,
        to_field_name="name",
    )
    timestamp = filters.DateTimeFromToRangeFilter()
    seller = filters.CharFilter(field_name="external_user_id", label="Seller")
    products = filters.RangeFilter(label="# Products sold (between)")
    price = filters.RangeFilter(field_name="total", label="Total (between)")

    class Meta:
        model = PosTransaction
        fields = {}

    @property
    def qs(self):
        """Add annotations here to make sure they are filterable."""
        self.queryset = PosTransaction.objects.filter(
            pos__team__camp=self.request.camp,
        ).annotate(
            # annotate total number of sales
            products=models.Count("pos_sales"),
            # annotate total price
            total=models.Sum("pos_sales__sales_price"),
        )
        return super().qs


class PosSaleFilter(FilterSet):
    """FilterSet for PosSale filtering."""

    txid = filters.CharFilter(
        field_name="transaction__external_transaction_id",
        label="Transaction ID",
    )
    prodid = filters.CharFilter(field_name="product__external_id", label="Product ID")
    brand = filters.CharFilter(
        field_name="product__brand_name",
        lookup_expr="icontains",
        label="Brand",
    )
    name = filters.CharFilter(
        field_name="product__name",
        lookup_expr="icontains",
        label="Product Name",
    )
    description = filters.CharFilter(
        field_name="product__description",
        lookup_expr="icontains",
        label="Description",
    )
    size = filters.RangeFilter(field_name="product__unit_size", label="Size")
    unit = filters.ModelChoiceFilter(
        field_name="product__size_unit",
        queryset=get_size_unit_widget_data,
        to_field_name="size_unit",
    )
    tags = filters.CharFilter(
        field_name="product__tags",
        lookup_expr="icontains",
        label="Tags",
    )
    price = filters.RangeFilter(field_name="sales_price", label="Price")
    pos = filters.ModelChoiceFilter(
        field_name="transaction__pos__name",
        queryset=get_pos_widget_data,
        to_field_name="name",
    )
    timestamp = filters.DateTimeFromToRangeFilter(field_name="transaction__timestamp")
    cost = filters.RangeFilter(label="Cost")
    profit = filters.RangeFilter(label="Profit")

    class Meta:
        model = PosSale
        fields = {}

    @property
    def qs(self):
        """Add annotations here to make sure they are filterable."""
        # define subq for getting latest product cost
        latest_cost = PosProductCost.objects.filter(
            product__uuid=models.OuterRef("product__uuid"),
            camp=self.request.camp,
        ).order_by("-timestamp")

        self.queryset = PosSale.objects.filter(
            transaction__pos__team__camp=self.request.camp,
        ).annotate(
            cost=models.functions.Coalesce(
                models.Subquery(latest_cost.values("product_cost")[:1]),
                0,
                output_field=models.DecimalField(),
            ),
            profit=models.Sum(models.F("sales_price") - models.F("cost")),
        )
        return super().qs


class PosProductCostFilter(FilterSet):
    """FilterSet for PosProductCost filtering."""

    brand = filters.CharFilter(
        field_name="product__brand_name",
        lookup_expr="icontains",
        label="Brand",
    )
    name = filters.CharFilter(
        field_name="product__name",
        lookup_expr="icontains",
        label="Product Name",
    )
    description = filters.CharFilter(
        field_name="product__description",
        lookup_expr="icontains",
        label="Description",
    )
    prodid = filters.CharFilter(field_name="product__external_id", label="Product ID")
    size = filters.RangeFilter(field_name="product__unit_size", label="Size")
    unit = filters.ModelChoiceFilter(
        field_name="product__size_unit",
        queryset=get_size_unit_widget_data,
        to_field_name="size_unit",
    )
    tags = filters.CharFilter(
        field_name="product__tags",
        lookup_expr="icontains",
        label="Tags",
    )
    timestamp = filters.DateTimeFromToRangeFilter()
    cost = filters.RangeFilter(field_name="product_cost", label="Product Cost")

    class Meta:
        model = PosProductCost
        fields = {}

    @property
    def qs(self):
        """Only show costs for current camp."""
        self.queryset = PosProductCost.objects.filter(camp=self.request.camp)
        return super().qs
