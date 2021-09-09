import csv
import logging
from io import StringIO

from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from camps.mixins import CampViewMixin
from economy.models import (
    Bank,
    BankAccount,
    BankTransaction,
    Chain,
    ClearhausSettlement,
    CoinifyBalance,
    CoinifyInvoice,
    CoinifyPayout,
    Credebtor,
    EpayTransaction,
    Expense,
    Reimbursement,
    Revenue,
)
from economy.utils import CoinifyCSVImporter, import_clearhaus_csv, import_epay_csv

from ..forms import BankCSVForm, ClearhausSettlementForm, CoinifyCSVForm, EpayCSVForm
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
# BANK, ACCOUNTS, TRANSACTIONS


class BankListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Bank
    template_name = "bank_list.html"


class BankDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Bank
    template_name = "bank_detail.html"
    pk_url_kwarg = "bank_uuid"


class BankCSVUploadView(CampViewMixin, EconomyTeamPermissionMixin, FormView):
    form_class = BankCSVForm
    template_name = "bank_csv_upload_form.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.bank = Bank.objects.get(pk=kwargs["bank_uuid"])

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["bank"] = self.bank
        return form_kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["bank"] = self.bank
        return context

    def form_valid(self, form):
        for file_id, file_handle in form.files.items():
            account = BankAccount.objects.get(pk=file_id)
            csvdata = file_handle.read().decode("utf-8-sig")
            reader = csv.reader(StringIO(csvdata), delimiter=";", quotechar='"')
            imported = account.import_csv(reader)
            if imported:
                messages.success(
                    self.request,
                    f"Successfully imported {imported} new transactions for bank account {account.name} ({account.pk})",
                )
            else:
                messages.info(
                    self.request,
                    f"No new transactions were created for bank account {account.name} ({account.pk}). Transaction text descriptions may have been updated.",
                )
        return redirect(
            reverse(
                "backoffice:bank_detail",
                kwargs={"camp_slug": self.camp.slug, "bank_uuid": self.bank.pk},
            )
        )


class BankAccountDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = BankAccount
    template_name = "bankaccount_detail.html"
    pk_url_kwarg = "bankaccount_uuid"


class BankTransactionDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = BankTransaction
    template_name = "banktransaction_detail.html"
    pk_url_kwarg = "banktransaction_uuid"


################################
# COINIFY


class CoinifyDashboardView(CampViewMixin, EconomyTeamPermissionMixin, TemplateView):
    template_name = "coinify_dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            latest = CoinifyBalance.objects.latest()
            context["balance"] = {
                "when": latest.date,
                "btc": latest.btc,
                "eur": latest.eur,
                "dkk": latest.dkk,
            }
        except CoinifyBalance.DoesNotExist:
            context["balance"] = None

        context["invoices"] = CoinifyInvoice.objects.count()
        context["payouts"] = CoinifyPayout.objects.count()
        context["balances"] = CoinifyBalance.objects.count()
        return context


class CoinifyInvoiceListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = CoinifyInvoice
    template_name = "coinifyinvoice_list.html"


class CoinifyPayoutListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = CoinifyPayout
    template_name = "coinifypayout_list.html"


class CoinifyBalanceListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = CoinifyBalance
    template_name = "coinifybalance_list.html"


class CoinifyCSVImportView(CampViewMixin, EconomyTeamPermissionMixin, FormView):
    form_class = CoinifyCSVForm
    template_name = "coinify_csv_upload_form.html"

    def form_valid(self, form):
        if "invoices" in form.files:
            csvdata = form.files["invoices"].read().decode("utf-8-sig")
            reader = csv.reader(StringIO(csvdata), delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_invoice_csv(reader)
            if created:
                messages.success(
                    self.request,
                    f"Invoices CSV processed OK. Successfully imported {created} new Coinify invoices.",
                )
            else:
                messages.info(
                    self.request,
                    "Invoices CSV processed OK. No new Coinify invoices were created.",
                )

        if "payouts" in form.files:
            csvdata = form.files["payouts"].read().decode("utf-8-sig")
            reader = csv.reader(StringIO(csvdata), delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_payout_csv(reader)
            if created:
                messages.success(
                    self.request,
                    f"Payouts CSV processed OK. Successfully imported {created} new Coinify payouts.",
                )
            else:
                messages.info(
                    self.request,
                    "Payouts CSV processed OK. No new Coinify payouts were created.",
                )

        if "balances" in form.files:
            csvdata = form.files["balances"].read().decode("utf-8-sig")
            reader = csv.reader(StringIO(csvdata), delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_balance_csv(reader)
            if created:
                messages.success(
                    self.request,
                    f"Balances CSV processed OK. Successfully imported {created} new Coinify balances.",
                )
            else:
                messages.info(
                    self.request,
                    "Balances CSV processed OK. No new Coinify balances were created.",
                )

        return redirect(
            reverse(
                "backoffice:coinify_dashboard",
                kwargs={"camp_slug": self.camp.slug},
            )
        )


################################
# EPAY / BAMBORA / CLEARHAUS


class EpayTransactionListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = EpayTransaction
    template_name = "epaytransaction_list.html"


class EpayCSVImportView(CampViewMixin, EconomyTeamPermissionMixin, FormView):
    form_class = EpayCSVForm
    template_name = "epay_csv_upload_form.html"

    def form_valid(self, form):
        if "transactions" in form.files:
            csvdata = form.files["transactions"].read().decode("utf-8-sig")
            reader = csv.reader(StringIO(csvdata), delimiter=";", quotechar='"')
            created = import_epay_csv(reader)
            if created:
                messages.success(
                    self.request,
                    f"ePay Transactions CSV processed OK. Successfully imported {created} new ePay Transactions.",
                )
            else:
                messages.info(
                    self.request,
                    "ePay Transactions CSV processed OK. No new ePay Transactions were created.",
                )

        return redirect(
            reverse(
                "backoffice:epaytransaction_list",
                kwargs={"camp_slug": self.camp.slug},
            )
        )


class ClearhausSettlementListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = ClearhausSettlement
    template_name = "clearhaus_settlement_list.html"


class ClearhausSettlementDetailView(
    CampViewMixin, EconomyTeamPermissionMixin, DetailView
):
    model = ClearhausSettlement
    template_name = "clearhaus_settlement_detail.html"
    pk_url_kwarg = "settlement_uuid"
    context_object_name = "cs"


class ClearhausSettlementImportView(
    CampViewMixin, EconomyTeamPermissionMixin, FormView
):
    form_class = ClearhausSettlementForm
    template_name = "clearhaus_csv_upload_form.html"

    def form_valid(self, form):
        if "settlements" in form.files:
            csvdata = form.files["settlements"].read().decode("utf-8-sig")
            reader = csv.reader(StringIO(csvdata), delimiter=",", quotechar='"')
            created = import_clearhaus_csv(reader)
            if created:
                messages.success(
                    self.request,
                    f"Clearhaus Settlements CSV processed OK. Successfully imported {created} new Clearhaus Settlements.",
                )
            else:
                messages.info(
                    self.request,
                    "Clearhaus Settlements CSV processed OK. No new Clearhaus Settlements created, but some might have been updated.",
                )

        return redirect(
            reverse(
                "backoffice:clearhaussettlement_list",
                kwargs={"camp_slug": self.camp.slug},
            )
        )
