import csv
import logging

from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from camps.mixins import CampViewMixin
from economy.models import Chain, Credebtor, Expense, Reimbursement, Revenue
from shop.models import Invoice

from ..mixins import EconomyTeamPermissionMixin

logger = logging.getLogger("bornhack.%s" % __name__)


################################
# CHAINS & CREDEBTORS


class ChainListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Chain
    template_name = "chain_list_backoffice.html"

    def get_queryset(self, *args, **kwargs):
        """Annotate the total count and amount for expenses and revenues for all credebtors in each chain."""
        qs = Chain.objects.annotate(
            camp_expenses_amount=Sum(
                "credebtors__expenses__amount",
                filter=Q(credebtors__expenses__camp=self.camp),
                distinct=True,
            ),
            camp_expenses_count=Count(
                "credebtors__expenses",
                filter=Q(credebtors__expenses__camp=self.camp),
                distinct=True,
            ),
            camp_revenues_amount=Sum(
                "credebtors__revenues__amount",
                filter=Q(credebtors__revenues__camp=self.camp),
                distinct=True,
            ),
            camp_revenues_count=Count(
                "credebtors__revenues",
                filter=Q(credebtors__revenues__camp=self.camp),
                distinct=True,
            ),
        )
        return qs


class ChainDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Chain
    template_name = "chain_detail_backoffice.html"
    slug_url_kwarg = "chain_slug"

    def get_queryset(self, *args, **kwargs):
        """Annotate the Chain object with the camp filtered expense and revenue info."""
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.annotate(
            camp_expenses_amount=Sum(
                "credebtors__expenses__amount",
                filter=Q(credebtors__expenses__camp=self.camp),
                distinct=True,
            ),
            camp_expenses_count=Count(
                "credebtors__expenses",
                filter=Q(credebtors__expenses__camp=self.camp),
                distinct=True,
            ),
            camp_revenues_amount=Sum(
                "credebtors__revenues__amount",
                filter=Q(credebtors__revenues__camp=self.camp),
                distinct=True,
            ),
            camp_revenues_count=Count(
                "credebtors__revenues",
                filter=Q(credebtors__revenues__camp=self.camp),
                distinct=True,
            ),
        )
        return qs

    def get_context_data(self, *args, **kwargs):
        """Add credebtors, expenses and revenues to the context in camp-filtered versions."""
        context = super().get_context_data(*args, **kwargs)

        # include credebtors as a seperate queryset with annotations for total number and
        # amount of expenses and revenues
        context["credebtors"] = Credebtor.objects.filter(
            chain=self.get_object()
        ).annotate(
            camp_expenses_amount=Sum(
                "expenses__amount", filter=Q(expenses__camp=self.camp), distinct=True
            ),
            camp_expenses_count=Count(
                "expenses", filter=Q(expenses__camp=self.camp), distinct=True
            ),
            camp_revenues_amount=Sum(
                "revenues__amount", filter=Q(revenues__camp=self.camp), distinct=True
            ),
            camp_revenues_count=Count(
                "revenues", filter=Q(revenues__camp=self.camp), distinct=True
            ),
        )

        # Include expenses and revenues for the Chain in context as seperate querysets,
        # since accessing them through the relatedmanager returns for all camps
        context["expenses"] = Expense.objects.filter(
            camp=self.camp, creditor__chain=self.get_object()
        ).prefetch_related("responsible_team", "user", "creditor")
        context["revenues"] = Revenue.objects.filter(
            camp=self.camp, debtor__chain=self.get_object()
        ).prefetch_related("responsible_team", "user", "debtor")
        return context


class CredebtorDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Credebtor
    template_name = "credebtor_detail_backoffice.html"
    slug_url_kwarg = "credebtor_slug"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["expenses"] = (
            self.get_object()
            .expenses.filter(camp=self.camp)
            .prefetch_related("responsible_team", "user", "creditor")
        )
        context["revenues"] = (
            self.get_object()
            .revenues.filter(camp=self.camp)
            .prefetch_related("responsible_team", "user", "debtor")
        )
        return context


################################
# EXPENSES


class ExpenseListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Expense
    template_name = "expense_list_backoffice.html"

    def get_queryset(self, **kwargs):
        """
        Exclude unapproved expenses, they are shown seperately
        """
        queryset = super().get_queryset(**kwargs)
        return queryset.exclude(approved__isnull=True).prefetch_related(
            "creditor",
            "user",
            "responsible_team",
        )

    def get_context_data(self, **kwargs):
        """
        Include unapproved expenses seperately
        """
        context = super().get_context_data(**kwargs)
        context["unapproved_expenses"] = Expense.objects.filter(
            camp=self.camp, approved__isnull=True
        ).prefetch_related(
            "creditor",
            "user",
            "responsible_team",
        )
        return context


class ExpenseDetailView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Expense
    template_name = "expense_detail_backoffice.html"
    fields = ["notes"]

    def form_valid(self, form):
        """
        We have two submit buttons in this form, Approve and Reject
        """
        expense = form.save()
        if "approve" in form.data:
            # approve button was pressed
            expense.approve(self.request)
        elif "reject" in form.data:
            # reject button was pressed
            expense.reject(self.request)
        else:
            messages.error(self.request, "Unknown submit action")
        return redirect(
            reverse("backoffice:expense_list", kwargs={"camp_slug": self.camp.slug})
        )


######################################
# REIMBURSEMENTS


class ReimbursementListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Reimbursement
    template_name = "reimbursement_list_backoffice.html"


class ReimbursementDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Reimbursement
    template_name = "reimbursement_detail_backoffice.html"


class ReimbursementCreateUserSelectView(
    CampViewMixin, EconomyTeamPermissionMixin, ListView
):
    template_name = "reimbursement_create_userselect.html"

    def get_queryset(self):
        queryset = User.objects.filter(
            id__in=Expense.objects.filter(
                camp=self.camp,
                reimbursement__isnull=True,
                paid_by_bornhack=False,
                approved=True,
            )
            .values_list("user", flat=True)
            .distinct()
        )
        return queryset


class ReimbursementCreateView(CampViewMixin, EconomyTeamPermissionMixin, CreateView):
    model = Reimbursement
    template_name = "reimbursement_create.html"
    fields = ["notes", "paid"]

    def dispatch(self, request, *args, **kwargs):
        """Get the user from kwargs"""
        self.reimbursement_user = get_object_or_404(User, pk=kwargs["user_id"])

        # get response now so we have self.camp available below
        response = super().dispatch(request, *args, **kwargs)

        # return the response
        return response

    def get(self, request, *args, **kwargs):
        # does this user have any approved and un-reimbursed expenses?
        if not self.reimbursement_user.expenses.filter(
            reimbursement__isnull=True, approved=True, paid_by_bornhack=False
        ):
            messages.error(
                request, "This user has no approved and unreimbursed expenses!"
            )
            return redirect(
                reverse("backoffice:index", kwargs={"camp_slug": self.camp.slug})
            )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expenses"] = Expense.objects.filter(
            user=self.reimbursement_user,
            approved=True,
            reimbursement__isnull=True,
            paid_by_bornhack=False,
        )
        context["total_amount"] = context["expenses"].aggregate(Sum("amount"))
        context["reimbursement_user"] = self.reimbursement_user
        return context

    def form_valid(self, form):
        """
        Set user and camp for the Reimbursement before saving
        """
        # get the expenses for this user
        expenses = Expense.objects.filter(
            user=self.reimbursement_user,
            approved=True,
            reimbursement__isnull=True,
            paid_by_bornhack=False,
        )
        if not expenses:
            messages.error(self.request, "No expenses found")
            return redirect(
                reverse(
                    "backoffice:reimbursement_list",
                    kwargs={"camp_slug": self.camp.slug},
                )
            )

        # do we have an Economy team for this camp?
        if not self.camp.economy_team:
            messages.error(self.request, "No economy team found")
            return redirect(
                reverse(
                    "backoffice:reimbursement_list",
                    kwargs={"camp_slug": self.camp.slug},
                )
            )

        # create reimbursement in database
        reimbursement = form.save(commit=False)
        reimbursement.reimbursement_user = self.reimbursement_user
        reimbursement.user = self.request.user
        reimbursement.camp = self.camp
        reimbursement.save()

        # add all expenses to reimbursement
        for expense in expenses:
            expense.reimbursement = reimbursement
            expense.save()

        # create payback expense for this reimbursement
        reimbursement.create_payback_expense()

        messages.success(
            self.request,
            f"Reimbursement {reimbursement} has been created with payback expense {reimbursement.payback_expense}"
            % (reimbursement.pk, timezone.now()),
        )
        return redirect(
            reverse(
                "backoffice:reimbursement_detail",
                kwargs={"camp_slug": self.camp.slug, "pk": reimbursement.pk},
            )
        )


class ReimbursementUpdateView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Reimbursement
    template_name = "reimbursement_form.html"
    fields = ["notes", "paid"]

    def get_success_url(self):
        return reverse(
            "backoffice:reimbursement_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.get_object().pk},
        )


class ReimbursementDeleteView(CampViewMixin, EconomyTeamPermissionMixin, DeleteView):
    model = Reimbursement
    template_name = "reimbursement_delete.html"
    fields = ["notes", "paid"]

    def get(self, request, *args, **kwargs):
        if self.get_object().paid:
            messages.error(
                request,
                "This reimbursement has already been paid so it cannot be deleted",
            )
            return redirect(
                reverse(
                    "backoffice:reimbursement_list",
                    kwargs={"camp_slug": self.camp.slug},
                )
            )
        # continue with the request
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request, f"Reimbursement {self.kwargs['pk']} deleted successfully!"
        )
        return reverse(
            "backoffice:reimbursement_list",
            kwargs={"camp_slug": self.camp.slug},
        )


################################
# REVENUES


class RevenueListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Revenue
    template_name = "revenue_list_backoffice.html"

    def get_queryset(self, **kwargs):
        """
        Exclude unapproved revenues, they are shown seperately
        """
        queryset = super().get_queryset(**kwargs)
        return queryset.exclude(approved__isnull=True).prefetch_related(
            "debtor",
            "user",
            "responsible_team",
        )

    def get_context_data(self, **kwargs):
        """
        Include unapproved revenues seperately
        """
        context = super().get_context_data(**kwargs)
        context["unapproved_revenues"] = Revenue.objects.filter(
            camp=self.camp, approved__isnull=True
        )
        return context


class RevenueDetailView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Revenue
    template_name = "revenue_detail_backoffice.html"
    fields = ["notes"]

    def form_valid(self, form):
        """
        We have two submit buttons in this form, Approve and Reject
        """
        revenue = form.save()
        if "approve" in form.data:
            # approve button was pressed
            revenue.approve(self.request)
        elif "reject" in form.data:
            # reject button was pressed
            revenue.reject(self.request)
        else:
            messages.error(self.request, "Unknown submit action")
        return redirect(
            reverse("backoffice:revenue_list", kwargs={"camp_slug": self.camp.slug})
        )


################################
# ORDERS & INVOICES


class InvoiceListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Invoice
    template_name = "invoice_list.html"


class InvoiceListCSVView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    """
    CSV export of invoices for bookkeeping stuff
    """

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="bornhack-infoices-{timezone.now()}.csv"'
        writer = csv.writer(response)
        writer.writerow(["invoice", "invoice_date", "amount_dkk", "order", "paid"])
        for invoice in Invoice.objects.all().order_by("-id"):
            writer.writerow(
                [
                    invoice.id,
                    invoice.created.date(),
                    invoice.order.total
                    if invoice.order
                    else invoice.customorder.amount,
                    invoice.get_order,
                    invoice.get_order.paid,
                ]
            )
        return response
