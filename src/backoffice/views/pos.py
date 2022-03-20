import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import UpdateView

from ..mixins import OrgaTeamPermissionMixin
from ..mixins import PosViewMixin
from ..mixins import RaisePermissionRequiredMixin
from camps.mixins import CampViewMixin
from economy.models import Pos
from economy.models import PosReport
from teams.models import Team

logger = logging.getLogger("bornhack.%s" % __name__)


class PosListView(CampViewMixin, RaisePermissionRequiredMixin, ListView):
    """Show a list of Pos this user has access to (through team memberships)."""

    permission_required = "camps.backoffice_permission"
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
    fields = ["name", "team"]

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
        context["form"].fields[
            "pos_responsible"
        ].queryset = self.pos.team.responsible_members.all()
        return context

    def form_valid(self, form):
        """
        Set Pos before saving
        """
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


class PosReportUpdateView(PosViewMixin, UpdateView):
    """Use this view to update PosReports."""

    model = PosReport
    fields = [
        "date",
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
        context["form"].fields[
            "pos_responsible"
        ].queryset = self.pos.team.responsible_members.all()
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
