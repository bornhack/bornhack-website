import json
import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from camps.mixins import CampViewMixin
from economy.filters import PosProductCostFilter
from economy.filters import PosProductFilter
from economy.filters import PosSaleFilter
from economy.filters import PosTransactionFilter
from economy.models import Expense
from economy.models import Pos
from economy.models import PosProduct
from economy.models import PosProductCost
from economy.models import PosReport
from economy.models import PosSale
from economy.models import PosTransaction
from economy.tables import PosProductCostTable
from economy.tables import PosProductTable
from economy.tables import PosSaleTable
from economy.tables import PosTransactionTable
from economy.utils import import_pos_sales_json
from teams.models import Team
from utils.mixins import AnyTeamPosRequiredMixin

from ..forms import PosSalesJSONForm
from ..mixins import OrgaTeamPermissionMixin
from ..mixins import PosViewMixin

logger = logging.getLogger("bornhack.%s" % __name__)


class PosListView(CampViewMixin, AnyTeamPosRequiredMixin, ListView):
    """Show a list of Pos this user has access to (through team pos permissions)."""

    model = Pos
    template_name = "pos_list.html"


class PosDetailView(PosViewMixin, DetailView):
    """Show details for a Pos."""

    model = Pos
    template_name = "pos_detail.html"
    slug_url_kwarg = "pos_slug"


class PosCreateView(CampViewMixin, OrgaTeamPermissionMixin, CreateView):
    """Create a new Pos (orga only)."""

    model = Pos
    template_name = "pos_form.html"
    fields = ["name", "team", "external_id"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"].fields["team"].queryset = Team.objects.filter(camp=self.camp)
        return context


class PosUpdateView(CampViewMixin, OrgaTeamPermissionMixin, UpdateView):
    """Update a Pos."""

    model = Pos
    template_name = "pos_form.html"
    slug_url_kwarg = "pos_slug"
    fields = ["name", "team"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"].fields["team"].queryset = Team.objects.filter(camp=self.camp)
        return context


class PosDeleteView(CampViewMixin, OrgaTeamPermissionMixin, DeleteView):
    model = Pos
    template_name = "pos_delete.html"
    slug_url_kwarg = "pos_slug"

    def delete(self, *args, **kwargs):
        self.get_object().pos_reports.all().delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            "The Pos and all related PosReports has been deleted",
        )
        return reverse("backoffice:pos_list", kwargs={"camp_slug": self.camp.slug})


# ################## POSREPORT VIEWS START #########################


class PosReportCreateView(PosViewMixin, CreateView):
    """Use this view to create new PosReports."""

    model = PosReport
    fields = ["period", "bank_responsible", "pos_responsible", "comments"]
    template_name = "posreport_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"].fields["bank_responsible"].queryset = Team.objects.get(
            camp=self.camp,
            name="Orga",
        ).approved_members.all()
        context["form"].fields["pos_responsible"].queryset = self.pos.team.leads.all()
        return context

    def form_valid(self, form):
        """Set Pos before saving"""
        pr = form.save(commit=False)
        pr.pos = self.pos
        pr.save()
        messages.success(self.request, "New PosReport created successfully!")
        return redirect(
            reverse(
                "backoffice:posreport_detail",
                kwargs={
                    "camp_slug": self.camp.slug,
                    "pos_slug": self.pos.slug,
                    "posreport_uuid": pr.uuid,
                },
            ),
        )


class PosReportListView(PosViewMixin, DetailView):
    """Show a list of PosReports for a Pos."""

    model = Pos
    template_name = "posreport_list.html"
    slug_url_kwarg = "pos_slug"


class PosReportUpdateView(PosViewMixin, UpdateView):
    """Use this view to update PosReports."""

    model = PosReport
    fields = [
        "period",
        "bank_responsible",
        "pos_responsible",
        "hax_sold_izettle",
        "dkk_sales_izettle",
        "comments",
    ]
    template_name = "posreport_form.html"
    pk_url_kwarg = "posreport_uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"].fields["bank_responsible"].queryset = Team.objects.get(
            camp=self.camp,
            name="Orga",
        ).approved_members.all()
        context["form"].fields["pos_responsible"].queryset = self.pos.team.leads.all()
        return context


class PosReportDetailView(PosViewMixin, DetailView):
    """Show details for a PosReport."""

    model = PosReport
    template_name = "posreport_detail.html"
    pk_url_kwarg = "posreport_uuid"


class PosReportBankCountStartView(PosViewMixin, UpdateView):
    """The bank responsible for a PosReport uses this view to add day-start HAX and DKK counts to a PosReport."""

    model = PosReport
    template_name = "posreport_form.html"
    fields = [
        "bank_count_dkk_start",
        "bank_count_hax5_start",
        "bank_count_hax10_start",
        "bank_count_hax20_start",
        "bank_count_hax50_start",
        "bank_count_hax100_start",
    ]
    pk_url_kwarg = "posreport_uuid"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        if self.request.user != self.get_object().bank_responsible:
            raise PermissionDenied("Only the bank responsible can do this")


class PosReportBankCountEndView(PosViewMixin, UpdateView):
    """The bank responsible for a PosReport uses this view to add day-end HAX and DKK counts to a PosReport."""

    model = PosReport
    template_name = "posreport_form.html"
    fields = [
        "bank_count_dkk_end",
        "bank_count_hax5_end",
        "bank_count_hax10_end",
        "bank_count_hax20_end",
        "bank_count_hax50_end",
        "bank_count_hax100_end",
    ]
    pk_url_kwarg = "posreport_uuid"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        if self.request.user != self.get_object().bank_responsible:
            raise PermissionDenied("Only the bank responsible can do this")


class PosReportPosCountStartView(PosViewMixin, UpdateView):
    """The Pos responsible for a PosReport uses this view to add day-start HAX and DKK counts to a PosReport."""

    model = PosReport
    template_name = "posreport_form.html"
    fields = [
        "pos_count_dkk_start",
        "pos_count_hax5_start",
        "pos_count_hax10_start",
        "pos_count_hax20_start",
        "pos_count_hax50_start",
        "pos_count_hax100_start",
    ]
    pk_url_kwarg = "posreport_uuid"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        if self.request.user != self.get_object().pos_responsible:
            raise PermissionDenied("Only the Pos responsible can do this")


class PosReportPosCountEndView(PosViewMixin, UpdateView):
    """The Pos responsible for a PosReport uses this view to add day-end HAX and DKK counts to a PosReport."""

    model = PosReport
    template_name = "posreport_form.html"
    fields = [
        "pos_count_dkk_end",
        "pos_count_hax5_end",
        "pos_count_hax10_end",
        "pos_count_hax20_end",
        "pos_count_hax50_end",
        "pos_count_hax100_end",
        "pos_json",
    ]
    pk_url_kwarg = "posreport_uuid"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        if self.request.user != self.get_object().pos_responsible:
            raise PermissionDenied("Only the pos responsible can do this")


# ################## POSREPORT VIEWS END #########################


class PosTransactionListView(
    CampViewMixin,
    AnyTeamPosRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    """A list of PosTransation objects."""

    model = PosTransaction
    template_name = "pos_transaction_list.html"
    table_class = PosTransactionTable
    filterset_class = PosTransactionFilter

    def get_context_data(self, *args, **kwargs):
        """Include the total (unfiltered) count."""
        context = super().get_context_data(*args, **kwargs)
        # transactions
        context["total_transactions"] = PosTransaction.objects.filter(
            pos__team__camp=self.camp,
        ).count()
        # total sales
        context["total_sales_count"] = PosSale.objects.filter(
            transaction__pos__team__camp=self.camp,
        ).count()
        context["total_sales_sum"] = PosSale.objects.filter(
            transaction__pos__team__camp=self.camp,
        ).aggregate(models.Sum("sales_price"))["sales_price__sum"]
        # filtered sales
        filtered_totals = context["filter"].qs.aggregate(
            filtered_sales_count=models.Count("pos_sales"),
            filtered_sales_sum=models.Sum("pos_sales__sales_price"),
        )
        context.update(filtered_totals)
        return context


class PosSaleListView(
    CampViewMixin,
    AnyTeamPosRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    """A list of PosSale objects."""

    model = PosSale
    template_name = "pos_sale_list.html"
    table_class = PosSaleTable
    filterset_class = PosSaleFilter

    def get_context_data(self, *args, **kwargs):
        """Include the total (unfiltered) count and sums."""
        context = super().get_context_data(*args, **kwargs)
        context["total_sales_count"] = PosSale.objects.filter(
            transaction__pos__team__camp=self.camp,
        ).count()
        context["total_sales_sum"] = PosSale.objects.filter(
            transaction__pos__team__camp=self.camp,
        ).aggregate(models.Sum("sales_price"))["sales_price__sum"]
        context["filtered_sales_sum"] = context["filter"].qs.aggregate(
            models.Sum("sales_price"),
        )["sales_price__sum"]
        return context


class PosSalesImportView(CampViewMixin, OrgaTeamPermissionMixin, FormView):
    form_class = PosSalesJSONForm
    template_name = "pos_sales_json_upload_form.html"

    def form_valid(self, form):
        if "sales" in form.files:
            sales_data = json.loads(form.files["sales"].read().decode())
            products, transactions, sales = import_pos_sales_json(sales_data)
            messages.success(
                self.request,
                f"PoS sales json processed OK. Created {products} new products and {transactions} new transactions containing {sales} new sales.",
            )
        return redirect(
            reverse(
                "backoffice:epaytransaction_list",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


class PosProductListView(
    CampViewMixin,
    AnyTeamPosRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    """A list of PosProduct objects."""

    model = PosProduct
    template_name = "pos_product_list.html"
    table_class = PosProductTable
    filterset_class = PosProductFilter

    def get_context_data(self, *args, **kwargs):
        """Include the total (unfiltered) count."""
        context = super().get_context_data(*args, **kwargs)
        campfilter = models.Q(pos_sales__transaction__pos__team__camp=self.camp)
        context["total_products"] = PosProduct.objects.filter(campfilter).distinct().count()
        filtered_totals = context["filter"].qs.aggregate(
            filtered_sales_count=models.Count("pos_sales", filter=campfilter),
            filtered_sales_sum=models.Sum("pos_sales__sales_price", filter=campfilter),
        )
        context.update(filtered_totals)
        context["total_sales_count"] = PosProduct.objects.aggregate(
            total_sales_count=models.Count("pos_sales", filter=campfilter),
        )["total_sales_count"]
        context["total_sales_sum"] = PosProduct.objects.aggregate(
            total_sales_sum=models.Sum("pos_sales__sales_price", filter=campfilter),
        )["total_sales_sum"]
        return context


class PosProductUpdateView(CampViewMixin, OrgaTeamPermissionMixin, UpdateView):
    """Use this view to update PosProduct objects."""

    model = PosProduct
    fields = [
        "brand_name",
        "name",
        "description",
        "sales_price",
        "unit_size",
        "size_unit",
        "abv",
        "tags",
        "expenses",
    ]
    template_name = "posproduct_form.html"
    pk_url_kwarg = "posproduct_uuid"

    def get_success_url(self):
        return reverse(
            "backoffice:posproduct_list",
            kwargs={"camp_slug": self.camp.slug},
        )

    def get_context_data(self, **kwargs):
        """Only show relevant expenses."""
        context = super().get_context_data(**kwargs)
        pos_teams = Team.objects.filter(camp=self.camp, points_of_sale__isnull=False)
        expenses = Expense.objects.filter(
            camp=self.camp,
            responsible_team__in=pos_teams,
        )
        context["form"].fields["expenses"].queryset = expenses
        return context


class PosProductCostListView(
    CampViewMixin,
    AnyTeamPosRequiredMixin,
    SingleTableMixin,
    FilterView,
):
    """A list of PosProductCost objects."""

    model = PosProductCost
    template_name = "pos_product_cost_list.html"
    table_class = PosProductCostTable
    filterset_class = PosProductCostFilter

    def get_context_data(self, **kwargs):
        """Include total number of costs."""
        context = super().get_context_data(**kwargs)
        context["total_costs"] = PosProductCost.objects.filter(camp=self.camp).count()
        return context


class PosProductCostUpdateView(CampViewMixin, OrgaTeamPermissionMixin, UpdateView):
    """Use this view to update PosProductCost objects."""

    model = PosProductCost
    fields = [
        "product_cost",
        "timestamp",
    ]
    template_name = "posproductcost_form.html"
    pk_url_kwarg = "posproductcost_uuid"

    def get_success_url(self):
        return reverse(
            "backoffice:posproductcost_list",
            kwargs={"camp_slug": self.camp.slug},
        )
