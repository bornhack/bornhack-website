from __future__ import annotations

import csv
import logging
import zipfile
from io import StringIO

import magic
from django.contrib import messages
from django.db.models import Count
from django.db.models import Q
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from backoffice.forms import BankCSVForm
from backoffice.forms import ClearhausSettlementForm
from backoffice.forms import CoinifyCSVForm
from backoffice.forms import EpayCSVForm
from backoffice.forms import MobilePayCSVForm
from backoffice.forms import ZettleUploadForm
from backoffice.mixins import EconomyTeamPermissionMixin
from camps.mixins import CampViewMixin
from economy.models import AccountingExport
from economy.models import Bank
from economy.models import BankAccount
from economy.models import BankTransaction
from economy.models import Chain
from economy.models import ClearhausSettlement
from economy.models import CoinifyBalance
from economy.models import CoinifyInvoice
from economy.models import CoinifyPaymentIntent
from economy.models import CoinifyPayout
from economy.models import CoinifySettlement
from economy.models import Credebtor
from economy.models import EpayTransaction
from economy.models import Expense
from economy.models import MobilePayTransaction
from economy.models import Reimbursement
from economy.models import Revenue
from economy.models import ZettleBalance
from economy.models import ZettleReceipt
from economy.utils import AccountingExporter
from economy.utils import CoinifyCSVImporter
from economy.utils import MobilePayCSVImporter
from economy.utils import ZettleExcelImporter
from economy.utils import import_clearhaus_csv
from economy.utils import import_epay_csv
from utils.mixins import VerbUpdateView

logger = logging.getLogger(f"bornhack.{__name__}")


################################
# CHAINS & CREDEBTORS


class ChainListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Chain
    template_name = "chain_list_backoffice.html"

    def get_queryset(self, *args, **kwargs):
        """Annotate the total count and amount for expenses and revenues for all credebtors in each chain."""
        return Chain.objects.annotate(
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


class ChainDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Chain
    template_name = "chain_detail_backoffice.html"
    slug_url_kwarg = "chain_slug"

    def get_queryset(self, *args, **kwargs):
        """Annotate the Chain object with the camp filtered expense and revenue info."""
        qs = super().get_queryset(*args, **kwargs)
        return qs.annotate(
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

    def get_context_data(self, *args, **kwargs):
        """Add credebtors, expenses and revenues to the context in camp-filtered versions."""
        context = super().get_context_data(*args, **kwargs)

        # include credebtors as a seperate queryset with annotations for total number and
        # amount of expenses and revenues
        context["credebtors"] = Credebtor.objects.filter(
            chain=self.get_object(),
        ).annotate(
            camp_expenses_amount=Sum(
                "expenses__amount",
                filter=Q(expenses__camp=self.camp),
                distinct=True,
            ),
            camp_expenses_count=Count(
                "expenses",
                filter=Q(expenses__camp=self.camp),
                distinct=True,
            ),
            camp_revenues_amount=Sum(
                "revenues__amount",
                filter=Q(revenues__camp=self.camp),
                distinct=True,
            ),
            camp_revenues_count=Count(
                "revenues",
                filter=Q(revenues__camp=self.camp),
                distinct=True,
            ),
        )

        # Include expenses and revenues for the Chain in context as seperate querysets,
        # since accessing them through the relatedmanager returns for all camps
        context["expenses"] = Expense.objects.filter(
            camp=self.camp,
            creditor__chain=self.get_object(),
        ).prefetch_related("responsible_team", "user", "creditor")
        context["revenues"] = Revenue.objects.filter(
            camp=self.camp,
            debtor__chain=self.get_object(),
        ).prefetch_related("responsible_team", "user", "debtor")

        # Include past years expenses and revenues for the Chain in context as separate querysets
        context["past_expenses"] = Expense.objects.filter(
            camp__camp__lt=self.camp.camp,
            creditor__chain=self.get_object(),
        ).prefetch_related("responsible_team", "user", "creditor")
        context["past_revenues"] = Revenue.objects.filter(
            camp__camp__lt=self.camp.camp,
            debtor__chain=self.get_object(),
        ).prefetch_related("responsible_team", "user", "debtor")

        return context


class CredebtorDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Credebtor
    template_name = "credebtor_detail_backoffice.html"
    slug_url_kwarg = "credebtor_slug"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["expenses"] = (
            self.get_object().expenses.filter(camp=self.camp).prefetch_related("responsible_team", "user", "creditor")
        )
        context["revenues"] = (
            self.get_object().revenues.filter(camp=self.camp).prefetch_related("responsible_team", "user", "debtor")
        )
        return context


################################
# EXPENSES


class ExpenseListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Expense
    template_name = "expense_list_backoffice.html"

    def get_queryset(self, **kwargs):
        """Exclude unapproved expenses, they are shown seperately."""
        queryset = super().get_queryset(**kwargs)
        return queryset.exclude(approved__isnull=True).prefetch_related(
            "creditor",
            "user",
            "responsible_team",
        )

    def get_context_data(self, **kwargs):
        """Include unapproved expenses seperately."""
        context = super().get_context_data(**kwargs)
        context["unapproved_expenses"] = Expense.objects.filter(
            camp=self.camp,
            approved__isnull=True,
        ).prefetch_related(
            "creditor",
            "user",
            "responsible_team",
        )
        return context


class ExpenseDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Expense
    template_name = "expense_detail_backoffice.html"


class ExpenseUpdateView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Expense
    template_name = "expense_update_backoffice.html"
    fields = ["notes"]

    def form_valid(self, form):
        """We have three submit buttons in this form, Approve, Reject, and Save."""
        expense = form.save()
        if "approve" in form.data and not expense.approved:
            # approve button was pressed
            expense.approve(self.request)
        elif "reject" in form.data and not expense.approved:
            # reject button was pressed
            expense.reject(self.request)
        elif "save" in form.data:
            messages.success(self.request, "Expense updated")
        else:
            messages.error(self.request, "Unknown submit action or wrong expense status")
        return redirect(
            reverse("backoffice:expense_list", kwargs={"camp_slug": self.camp.slug}),
        )


######################################
# REIMBURSEMENTS


class ReimbursementListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Reimbursement
    template_name = "reimbursement_list_backoffice.html"


class ReimbursementDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Reimbursement
    template_name = "reimbursement_detail_backoffice.html"


class ReimbursementUpdateView(
    CampViewMixin,
    EconomyTeamPermissionMixin,
    VerbUpdateView,
):
    model = Reimbursement
    template_name = "reimbursement_form.html"
    fields = ["notes", "paid"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expenses"] = self.object.expenses.filter(paid_by_bornhack=False)
        context["total_amount"] = context["expenses"].aggregate(Sum("amount"))
        context["reimbursement_user"] = self.object.reimbursement_user
        context["cancelurl"] = reverse(
            "backoffice:reimbursement_list",
            kwargs={"camp_slug": self.camp.slug},
        )
        return context

    def get_success_url(self):
        return reverse(
            "backoffice:reimbursement_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.get_object().pk},
        )


class ReimbursementDeleteView(CampViewMixin, EconomyTeamPermissionMixin, DeleteView):
    model = Reimbursement
    template_name = "reimbursement_delete.html"

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
                ),
            )
        # continue with the request
        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            f"Reimbursement {self.kwargs['pk']} deleted successfully!",
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
        """Exclude unapproved revenues, they are shown seperately."""
        queryset = super().get_queryset(**kwargs)
        return queryset.exclude(approved__isnull=True).prefetch_related(
            "debtor",
            "user",
            "responsible_team",
        )

    def get_context_data(self, **kwargs):
        """Include unapproved revenues seperately."""
        context = super().get_context_data(**kwargs)
        context["unapproved_revenues"] = Revenue.objects.filter(
            camp=self.camp,
            approved__isnull=True,
        )
        return context


class RevenueDetailView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Revenue
    template_name = "revenue_detail_backoffice.html"
    fields = ["notes"]

    def form_valid(self, form):
        """We have two submit buttons in this form, Approve and Reject."""
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
            reverse("backoffice:revenue_list", kwargs={"camp_slug": self.camp.slug}),
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

    def setup(self, *args, **kwargs) -> None:
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
            ),
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

        context["payment_intents"] = CoinifyPaymentIntent.objects.count()
        context["settlements"] = CoinifySettlement.objects.count()
        context["invoices"] = CoinifyInvoice.objects.count()
        context["payouts"] = CoinifyPayout.objects.count()
        context["balances"] = CoinifyBalance.objects.count()
        return context


class CoinifyInvoiceListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = CoinifyInvoice
    template_name = "coinifyinvoice_list.html"


class CoinifyPaymentIntentListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = CoinifyPaymentIntent
    template_name = "coinifypayment_intent_list.html"


class CoinifyPayoutListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = CoinifyPayout
    template_name = "coinifypayout_list.html"


class CoinifyBalanceListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = CoinifyBalance
    template_name = "coinifybalance_list.html"


class CoinifySettlementListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = CoinifySettlement
    template_name = "coinifysettlement_list.html"


class CoinifyCSVImportView(CampViewMixin, EconomyTeamPermissionMixin, FormView):
    form_class = CoinifyCSVForm
    template_name = "coinify_csv_upload_form.html"

    def form_valid(self, form):
        if "payment_intents" in form.files:
            csvdata = form.files["payment_intents"].read().decode("utf-8-sig")
            reader = csv.reader(StringIO(csvdata), delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_payment_intent_csv(reader)
            if created:
                messages.success(
                    self.request,
                    f"Payment Intent CSV processed OK. Successfully imported {created} new Coinify payment intents.",
                )
            else:
                messages.info(
                    self.request,
                    "Payment Intent CSV processed OK. No new Coinify payment intents were created.",
                )

        if "settlements" in form.files:
            csvdata = form.files["settlements"].read().decode("utf-8-sig")
            reader = csv.reader(StringIO(csvdata), delimiter=",", quotechar='"')
            created = CoinifyCSVImporter.import_coinify_settlements_csv(reader)
            if created:
                messages.success(
                    self.request,
                    f"Settlements CSV processed OK. Successfully imported {created} new Coinify settlements.",
                )
            else:
                messages.info(
                    self.request,
                    "Settlements CSV processed OK. No new Coinify settlements were created.",
                )

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
            ),
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
            ),
        )


class ClearhausSettlementListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = ClearhausSettlement
    template_name = "clearhaus_settlement_list.html"


class ClearhausSettlementDetailView(
    CampViewMixin,
    EconomyTeamPermissionMixin,
    DetailView,
):
    model = ClearhausSettlement
    template_name = "clearhaus_settlement_detail.html"
    pk_url_kwarg = "settlement_uuid"
    context_object_name = "cs"


class ClearhausSettlementImportView(
    CampViewMixin,
    EconomyTeamPermissionMixin,
    FormView,
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
            ),
        )


################################
# ZETTLE (iZettle)


class ZettleDashboardView(CampViewMixin, EconomyTeamPermissionMixin, TemplateView):
    template_name = "zettle_dashboard.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            latest = ZettleBalance.objects.latest()
            context["balance"] = latest
        except ZettleBalance.DoesNotExist:
            context["balance"] = None

        context["receipts"] = ZettleReceipt.objects.count()
        context["balances"] = ZettleBalance.objects.count()
        return context


class ZettleReceiptListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = ZettleReceipt
    template_name = "zettlereceipt_list.html"


class ZettleBalanceListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = ZettleBalance
    template_name = "zettlebalance_list.html"


class ZettleDataImportView(CampViewMixin, EconomyTeamPermissionMixin, FormView):
    form_class = ZettleUploadForm
    template_name = "zettle_upload_form.html"

    def form_valid(self, form):
        if "balances" in form.files:
            df = ZettleExcelImporter.load_zettle_balances_excel(form.files["balances"])
            created = ZettleExcelImporter.import_zettle_balances_df(df)
            if created:
                messages.success(
                    self.request,
                    f"Zettle balances data processed OK. Successfully imported {created} new Zettle balances.",
                )
            else:
                messages.info(
                    self.request,
                    "Zettle balances data processed OK. No new Zettle balances created.",
                )

        if "receipts" in form.files:
            df = ZettleExcelImporter.load_zettle_receipts_excel(form.files["receipts"])
            created = ZettleExcelImporter.import_zettle_receipts_df(df)
            if created:
                messages.success(
                    self.request,
                    f"Zettle receipts data processed OK. Successfully imported {created} new Zettle receipts.",
                )
            else:
                messages.info(
                    self.request,
                    "Zettle receipts data processed OK. No new Zettle receipts created.",
                )

        return redirect(
            reverse(
                "backoffice:zettle_dashboard",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


################################
# MOBILEPAY


class MobilePayTransactionListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = MobilePayTransaction
    template_name = "mobilepaytransaction_list.html"


class MobilePayCSVImportView(CampViewMixin, EconomyTeamPermissionMixin, FormView):
    form_class = MobilePayCSVForm
    template_name = "mobilepay_csv_upload_form.html"

    def form_valid(self, form):
        if "transfers" in form.files:
            csvdata = form.files["transfers"].read().decode("utf-8-sig")
            reader = csv.reader(StringIO(csvdata), delimiter=";", quotechar='"')
            created = MobilePayCSVImporter.import_mobilepay_transfer_csv(reader)
            if created:
                messages.success(
                    self.request,
                    f"MobilePay Transfers/transactions CSV processed OK. Successfully imported {created} new MobilePay Transactions.",
                )
            else:
                messages.info(
                    self.request,
                    "MobilePay Transfers/transactions CSV processed OK. No new MobilePay Transactions created.",
                )

        if "sales" in form.files:
            csvdata = form.files["sales"].read().decode("utf-8-sig")
            reader = csv.reader(StringIO(csvdata), delimiter=";", quotechar='"')
            created = MobilePayCSVImporter.import_mobilepay_sales_csv(reader)
            if created:
                messages.success(
                    self.request,
                    f"MobilePay Sales CSV processed OK. Successfully imported {created} new MobilePay Transactions.",
                )
            else:
                messages.info(
                    self.request,
                    "MobilePay Sales CSV processed OK. No new MobilePay Transactions created.",
                )

        return redirect(
            reverse(
                "backoffice:mobilepaytransaction_list",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


################################
# ACCOUNTING EXPORT


class AccountingExportCreateView(CampViewMixin, EconomyTeamPermissionMixin, CreateView):
    template_name = "accountingexport_form.html"
    model = AccountingExport
    fields = ["date_from", "date_to", "comment"]

    def form_valid(self, form):
        """Gather data and create a zipfile with all of it."""
        # get the model instance
        export = form.save(commit=False)

        # initiate and run the exporter
        exporter = AccountingExporter(
            startdate=export.date_from,
            enddate=export.date_to,
        )
        exporter.doit()

        # add the archive to the model and save
        export.archive.save(
            f"bornhack_accounting_export_from_{export.date_from}_to_{export.date_to}_{export.uuid}.zip",
            exporter.archivedata,
        )

        # some feedback and redirect
        messages.success(
            self.request,
            f"Wrote archive file {export.archive.path} to disk, yay",
        )
        return redirect(
            reverse(
                "backoffice:accountingexport_list",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


class AccountingExportListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = AccountingExport
    template_name = "accountingexport_list.html"


class AccountingExportDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = AccountingExport
    template_name = "accountingexport_detail.html"
    pk_url_kwarg = "accountingexport_uuid"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        z = zipfile.ZipFile(self.get_object().archive.path)
        # we need a list of just filenames without the folder name
        sorted_names = z.namelist()
        sorted_names.sort()
        context["files"] = [f.split("/")[1] for f in sorted_names if "/" in f]
        return context


class AccountingExportUpdateView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = AccountingExport
    template_name = "accountingexport_form.html"
    pk_url_kwarg = "accountingexport_uuid"
    fields = ["comment"]

    def get_success_url(self):
        messages.success(
            self.request,
            f"Accounting Export {self.kwargs['accountingexport_uuid']} updated successfully!",
        )
        return reverse(
            "backoffice:accountingexport_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class AccountingExportDeleteView(CampViewMixin, EconomyTeamPermissionMixin, DeleteView):
    model = AccountingExport
    template_name = "accountingexport_delete.html"
    pk_url_kwarg = "accountingexport_uuid"

    def get_success_url(self):
        messages.success(
            self.request,
            f"Accounting Export {self.kwargs['accountingexport_uuid']} deleted successfully!",
        )
        return reverse(
            "backoffice:accountingexport_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class AccountingExportDownloadArchiveView(
    CampViewMixin,
    EconomyTeamPermissionMixin,
    DetailView,
):
    model = AccountingExport
    pk_url_kwarg = "accountingexport_uuid"

    def get(self, request, *args, **kwargs):
        ae = self.get_object()
        archive = ae.archive.read()
        mimetype = magic.from_buffer(archive, mime=True)
        response = HttpResponse(content_type=mimetype)
        response["Content-Disposition"] = (
            f"attachment; filename=bornhack_accounting_export_from_{ae.date_from}_to_{ae.date_to}_{ae.uuid}.zip"
        )
        response.write(archive)
        return response


class AccountingExportDownloadFileView(
    CampViewMixin,
    EconomyTeamPermissionMixin,
    DetailView,
):
    model = AccountingExport
    pk_url_kwarg = "accountingexport_uuid"

    def get(self, request, *args, **kwargs):
        ae = self.get_object()
        filename = kwargs["filename"]
        with zipfile.ZipFile(ae.archive.path) as z, z.open("bornhack_accounting_export/" + filename) as f:
            data = f.read()
        mimetype = magic.from_buffer(data, mime=True)
        response = HttpResponse(content_type=mimetype)
        response["Content-Disposition"] = f"attachment; filename={filename}"
        response.write(data)
        return response
