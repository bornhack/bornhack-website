import csv
import os
from datetime import datetime
from decimal import Decimal

import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.postgres.fields import DateTimeRangeField
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django_prometheus.models import ExportModelOperationsMixin

from shop.models import Product
from tickets.models import ShopTicket
from utils.models import CampRelatedModel
from utils.models import CreatedUpdatedModel
from utils.models import CreatedUpdatedUUIDModel
from utils.models import UUIDModel
from utils.slugs import unique_slugify

from .email import send_accountingsystem_expense_email
from .email import send_accountingsystem_revenue_email
from .email import send_expense_approved_email
from .email import send_expense_rejected_email
from .email import send_revenue_approved_email
from .email import send_revenue_rejected_email


class ChainManager(models.Manager):
    """ChainManager adds 'expenses_total' and 'revenues_total' to the Chain qs
    Also adds 'expenses_count' and 'revenues_count' and prefetches all expenses
    and revenues for the credebtors.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.prefetch_related(
            models.Prefetch("credebtors__expenses", to_attr="all_expenses"),
            models.Prefetch("credebtors__revenues", to_attr="all_revenues"),
        )
        qs = qs.annotate(
            all_expenses_amount=models.Sum(
                "credebtors__expenses__amount",
                distinct=True,
            ),
        )
        qs = qs.annotate(
            all_expenses_count=models.Count("credebtors__expenses", distinct=True),
        )
        qs = qs.annotate(
            all_revenues_amount=models.Sum(
                "credebtors__revenues__amount",
                distinct=True,
            ),
        )
        qs = qs.annotate(
            all_revenues_count=models.Count("credebtors__revenues", distinct=True),
        )
        return qs


class Chain(ExportModelOperationsMixin("chain"), CreatedUpdatedModel, UUIDModel):
    """A chain of Credebtors. Used to group when several Creditors/Debtors
    belong to the same Chain/company, like XL Byg stores or Netto stores.
    """

    class Meta:
        ordering = ["name"]

    objects = ChainManager()

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='A short name for this Chain, like "Netto" or "XL Byg". 100 characters or fewer.',
    )

    slug = models.SlugField(
        unique=True,
        blank=True,
        help_text="The url slug for this Chain. Leave blank to auto generate a slug.",
    )

    notes = models.TextField(
        help_text="Any notes for this Chain. Will be shown to anyone creating Expenses or Revenues for this Chain.",
        blank=True,
    )

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.all().values_list(
                    "slug",
                    flat=True,
                ),
            )
        super().save(**kwargs)

    @property
    def expenses(self):
        return Expense.objects.filter(creditor__chain__pk=self.pk)

    @property
    def revenues(self):
        return Revenue.objects.filter(debtor__chain__pk=self.pk)


class CredebtorManager(models.Manager):
    """CredebtorManager adds 'expenses_total' and 'revenues_total' to the Credebtor qs,
    and prefetches expenses and revenues for the credebtor(s).
    """

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.prefetch_related(
            models.Prefetch("expenses", to_attr="all_expenses"),
            models.Prefetch("revenues", to_attr="all_revenues"),
        )
        qs = qs.annotate(all_expenses_amount=models.Sum("expenses__amount"))
        qs = qs.annotate(all_revenues_amount=models.Sum("revenues__amount"))
        return qs


class Credebtor(
    ExportModelOperationsMixin("credebtor"),
    CreatedUpdatedModel,
    UUIDModel,
):
    """The Credebtor model represents the specific "instance" of a Chain,
    like "XL Byg Rønne" or "Netto Gelsted".
    The model is used for both creditors and debtors, since there is a
    lot of overlap between them.
    """

    class Meta:
        ordering = ["name"]
        unique_together = ("chain", "slug")

    objects = CredebtorManager()

    chain = models.ForeignKey(
        "economy.Chain",
        on_delete=models.PROTECT,
        related_name="credebtors",
        help_text="The Chain to which this Credebtor belongs.",
    )

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='The name of this Credebtor, like "XL Byg Rønne" or "Netto Gelsted". 100 characters or fewer.',
    )

    slug = models.SlugField(
        blank=True,
        help_text="The url slug for this Credebtor. Leave blank to auto generate a slug.",
    )

    address = models.TextField(help_text="The address of this Credebtor.")

    notes = models.TextField(
        blank=True,
        help_text="Any notes for this Credebtor. Shown when creating an Expense or Revenue for this Credebtor.",
    )

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        """Generate slug as needed"""
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.filter(
                    chain=self.chain,
                ).values_list("slug", flat=True),
            )
        super().save(**kwargs)


class Revenue(ExportModelOperationsMixin("revenue"), CampRelatedModel, UUIDModel):
    """The Revenue model represents any type of income for BornHack.

    Most Revenue objects will have a FK to the Invoice model,
    but only if the revenue relates directly to an Invoice in our system.

    Other Revenue objects (such as money returned from bottle deposits) will
    not have a related BornHack Invoice object.
    """

    camp = models.ForeignKey(
        "camps.Camp",
        on_delete=models.PROTECT,
        related_name="revenues",
        help_text="The camp to which this revenue belongs",
    )

    debtor = models.ForeignKey(
        "economy.Credebtor",
        on_delete=models.PROTECT,
        related_name="revenues",
        help_text="The Debtor to which this revenue belongs",
    )

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="revenues",
        help_text="The user who submitted this revenue",
    )

    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text="The amount of this revenue in DKK. Must match the amount on the documentation uploaded below.",
    )

    description = models.CharField(
        max_length=200,
        help_text="A short description of this revenue. Please keep it meningful as it helps the Economy team a lot when categorising revenue. 200 characters or fewer.",
    )

    invoice = models.ImageField(
        help_text="The invoice file for this revenue. Please make sure the amount on the invoice matches the amount you entered above. All common image formats are accepted, as well as PDF.",
        upload_to="revenues/",
    )

    invoice_date = models.DateField(
        help_text="The invoice date for this Revenue. This must match the invoice date on the documentation uploaded below. Format is YYYY-MM-DD.",
    )

    invoice_fk = models.ForeignKey(
        "shop.Invoice",
        on_delete=models.PROTECT,
        related_name="revenues",
        help_text="The Invoice object to which this Revenue object relates. Can be None if this revenue does not have a related BornHack Invoice.",
        blank=True,
        null=True,
    )

    responsible_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="revenues",
        help_text="The team to which this revenue belongs. When in doubt pick the Economy team.",
    )

    approved = models.BooleanField(
        blank=True,
        null=True,
        default=None,
        help_text="True if this Revenue has been approved by the responsible team. False if it has been rejected. Blank if noone has decided yet.",
    )

    notes = models.TextField(
        blank=True,
        help_text="Economy Team notes for this revenue. Only visible to the Economy team and the submitting user.",
    )

    def clean(self):
        if self.amount < 0:
            raise ValidationError("Amount of a Revenue object can not be negative")

    def get_backoffice_url(self):
        return reverse(
            "backoffice:revenue_detail",
            kwargs={"pk": self.pk, "camp_slug": self.camp.slug},
        )

    @property
    def invoice_filename(self):
        return os.path.basename(self.invoice.file.name)

    @property
    def approval_status(self):
        if self.approved is None:
            return "Pending approval"
        if self.approved:
            return "Approved"
        return "Rejected"

    def approve(self, request):
        """This method marks a revenue as approved.
        Approving a revenue triggers an email to the economy system, and another email to the user who submitted the revenue
        """
        if request.user == self.user:
            messages.error(
                request,
                "You cannot approve your own revenues, aka. the anti-stein-bagger defense",
            )
            return

        # mark as approved and save
        self.approved = True
        self.save()

        # send email to economic for this revenue
        send_accountingsystem_revenue_email(revenue=self)

        # send email to the user
        send_revenue_approved_email(revenue=self)

        # message to the browser
        messages.success(request, "Revenue %s approved" % self.pk)

    def reject(self, request):
        """This method marks a revenue as not approved.
        Not approving a revenue triggers an email to the user who submitted the revenue in the first place.
        """
        # mark as not approved and save
        self.approved = False
        self.save()

        # send email to the user
        send_revenue_rejected_email(revenue=self)

        # message to the browser
        messages.success(request, "Revenue %s rejected" % self.pk)


class Expense(ExportModelOperationsMixin("expense"), CampRelatedModel, UUIDModel):
    camp = models.ForeignKey(
        "camps.Camp",
        on_delete=models.PROTECT,
        related_name="expenses",
        help_text="The camp to which this expense belongs",
    )

    creditor = models.ForeignKey(
        "economy.Credebtor",
        on_delete=models.PROTECT,
        related_name="expenses",
        help_text="The Creditor to which this expense belongs",
    )

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="expenses",
        help_text="The user to which this expense belongs",
    )

    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text="The amount of this expense in DKK. Must match the amount on the invoice uploaded below.",
    )

    description = models.CharField(
        max_length=200,
        help_text="A short description of this expense. Please keep it meningful as it helps the Economy team a lot when categorising expenses. 200 characters or fewer.",
    )

    paid_by_bornhack = models.BooleanField(
        default=True,
        help_text="Leave checked if this expense was paid by BornHack. Uncheck if you need a reimbursement for this expense.",
    )

    invoice = models.ImageField(
        help_text="The invoice for this expense. Please make sure the amount on the invoice matches the amount you entered above. All common image formats are accepted.",
        upload_to="expenses/",
    )

    invoice_date = models.DateField(
        help_text="The invoice date for this Expense. This must match the invoice date on the documentation uploaded below. Format is YYYY-MM-DD.",
    )

    responsible_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="expenses",
        help_text="The team to which this Expense belongs. A team lead will need to approve the expense. When in doubt pick the Orga team.",
    )

    approved = models.BooleanField(
        blank=True,
        null=True,
        default=None,
        help_text="True if this expense has been approved by the responsible team. False if it has been rejected. Blank if noone has decided yet.",
    )

    reimbursement = models.ForeignKey(
        "economy.Reimbursement",
        on_delete=models.SET_NULL,
        related_name="expenses",
        null=True,
        blank=True,
        help_text="The reimbursement for this expense, if any. This is a dual-purpose field. If expense.paid_by_bornhack is true then expense.reimbursement references the reimbursement which this expense is created to cover. If expense.paid_by_bornhack is false then expense.reimbursement references the reimbursement which reimbursed this expense.",
    )

    notes = models.TextField(
        blank=True,
        help_text="Economy Team notes for this expense. Only visible to the Economy team and the submitting user.",
    )

    def clean(self):
        if self.amount < 0:
            raise ValidationError("Amount of an expense can not be negative")

    @property
    def invoice_filename(self):
        return os.path.basename(self.invoice.file.name)

    @property
    def approval_status(self):
        if self.approved is None:
            return "Pending approval"
        if self.approved:
            return "Approved"
        return "Rejected"

    def get_backoffice_url(self):
        return reverse(
            "backoffice:expense_detail",
            kwargs={"pk": self.pk, "camp_slug": self.camp.slug},
        )

    def approve(self, request):
        """This method marks an expense as approved.
        Approving an expense triggers an email to the economy system, and another email to the user who submitted the expense in the first place.
        """
        if request.user == self.user:
            messages.error(
                request,
                "You cannot approve your own expenses, aka. the anti-stein-bagger defense",
            )
            return

        # mark as approved and save
        self.approved = True
        self.save()

        # send email to economic for this expense
        send_accountingsystem_expense_email(expense=self)

        # send email to the user
        send_expense_approved_email(expense=self)

        # message to the browser
        messages.success(request, "Expense %s approved" % self.pk)

    def reject(self, request):
        """This method marks an expense as not approved.
        Not approving an expense triggers an email to the user who submitted the expense in the first place.
        """
        # mark as not approved and save
        self.approved = False
        self.save()

        # send email to the user
        send_expense_rejected_email(expense=self)

        # message to the browser
        messages.success(request, "Expense %s rejected" % self.pk)

    def __str__(self):
        return f"{self.responsible_team.name} Team - {self.amount} DKK - {self.creditor.name} - {self.description}"


class Reimbursement(
    ExportModelOperationsMixin("reimbursement"),
    CampRelatedModel,
    UUIDModel,
):
    """A reimbursement covers one or more expenses."""

    camp = models.ForeignKey(
        "camps.Camp",
        on_delete=models.PROTECT,
        related_name="reimbursements",
        help_text="The camp to which this reimbursement belongs",
    )

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="created_reimbursements",
        help_text="The user who created this reimbursement.",
    )

    reimbursement_user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="reimbursements",
        help_text="The user this reimbursement belongs to.",
    )

    bank_account = models.TextField(
        help_text="The bank account where you want the payment of this reimbursement transferred to. For transfers outside Denmark please include IBAN and BIC.",
    )

    notes = models.TextField(
        blank=True,
        help_text="Economy Team notes for this reimbursement. Only visible to the Economy team and the reimbursed user.",
    )

    paid = models.BooleanField(
        default=False,
        help_text="Check when this reimbursement has been paid to the user. Do not check until the bank transfer has been fully approved.",
    )

    def get_backoffice_url(self):
        return reverse(
            "backoffice:reimbursement_detail",
            kwargs={"pk": self.pk, "camp_slug": self.camp.slug},
        )

    @property
    def covered_expenses(self):
        """Returns a queryset of all expenses covered by this reimbursement. Excludes the expense which paid back the reimbursement."""
        return self.expenses.filter(paid_by_bornhack=False)

    @property
    def amount(self):
        """The total amount for a reimbursement is calculated by adding up the amounts for all the related expenses."""
        return self.expenses.filter(paid_by_bornhack=False).aggregate(
            models.Sum("amount"),
        )["amount__sum"]

    @property
    def payback_expense(self):
        """Return the expense created to pay back this reimbursement."""
        if self.expenses.filter(paid_by_bornhack=True).exists():
            return self.expenses.get(paid_by_bornhack=True)

    def create_payback_expense(self):
        """Create the expense to pay back this reimbursement."""
        if self.payback_expense:
            # we already have an expense created, just return that one
            return self.payback_expense

        # we need an economy team to do this
        if not self.camp.economy_team:
            return False

        # create the expense
        expense = Expense()
        expense.camp = self.camp
        expense.user = self.user
        expense.amount = self.amount
        expense.description = f"Payment of reimbursement {self.pk} to {self.reimbursement_user}"
        expense.paid_by_bornhack = True
        expense.responsible_team = self.camp.economy_team
        expense.approved = True
        expense.reimbursement = self
        expense.invoice_date = self.created
        expense.creditor = Credebtor.objects.get(name="Reimbursement")
        expense.invoice.save(
            "na.jpg",
            File(
                open(
                    os.path.join(settings.BASE_DIR, "static_src/img/na.jpg"),
                    "rb",
                ),
            ),
        )
        expense.save()
        return expense


##################################
# Point of Sale


class Pos(ExportModelOperationsMixin("pos"), CampRelatedModel, UUIDModel):
    """A Pos is a point-of-sale like the bar or infodesk."""

    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=255, help_text="The point-of-sale name")

    external_id = models.CharField(
        max_length=100,
        help_text="The external database ID of this pos location.",
    )

    slug = models.SlugField(
        max_length=255,
        blank=True,
        help_text="Url slug for this POS. Leave blank to generate based on POS name.",
    )

    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="points_of_sale",
        help_text="The Team managing this POS",
    )

    def __str__(self):
        return f"{self.name} POS ({self.camp})"

    def save(self, **kwargs):
        """Generate slug if needed."""
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.filter(
                    team__camp=self.team.camp,
                ).values_list("slug", flat=True),
            )
        super().save(**kwargs)

    @property
    def camp(self):
        return self.team.camp

    camp_filter = "team__camp"

    def get_absolute_url(self):
        return reverse(
            "backoffice:pos_detail",
            kwargs={"camp_slug": self.team.camp.slug, "pos_slug": self.slug},
        )

    def export_csv(self, period, workdir):
        """Write PosReports to a CSV file for the bookkeeper"""
        filename = f"bornhack_pos_{self.slug}_{period.lower}_{period.upper}.csv"
        with open(workdir / filename, "w", newline="") as f:
            posreports = self.pos_reports.filter(period__contained_by=period)
            writer = csv.writer(f, dialect="excel")
            writer.writerow(
                [
                    "bornhack_uuid",
                    "start_time",
                    "end_time",
                    "dkk_sales_izettle",
                    "hax_sold_izettle",
                    "hax_sold_website",
                    "dkk_start",
                    "dkk_end",
                    "dkk_balance",
                    "hax_start",
                    "hax_end",
                    "hax_balance",
                    "pos_transactions",
                ],
            )
            for pr in posreports:
                writer.writerow(
                    [
                        pr.pk,
                        pr.period.lower,
                        pr.period.upper,
                        pr.dkk_sales_izettle,
                        pr.hax_sold_izettle,
                        pr.hax_sold_website,
                        pr.bank_count_dkk_start,
                        pr.bank_count_dkk_end,
                        pr.dkk_balance,
                        pr.bank_start_hax,
                        pr.bank_end_hax,
                        pr.hax_balance,
                        pr.pos_json_sales[0],
                    ],
                )
        return (self, filename, posreports.count())

    @property
    def total_sales(self):
        """Return the sum of all sales in all transactions for this Pos."""
        return self.sales.aggregate(models.Sum("sales_price"))["sales_price__sum"]

    @property
    def sales(self):
        """Return a queryset of all sales in all transactions for this Pos."""
        return PosSale.objects.filter(transaction__pos=self)


class PosReport(ExportModelOperationsMixin("pos_report"), CampRelatedModel, UUIDModel):
    """A PosReport contains the HAX/DKK counts and the csv report from the POS system."""

    class Meta:
        ordering = ["period", "pos"]

    pos = models.ForeignKey(
        "economy.Pos",
        on_delete=models.PROTECT,
        related_name="pos_reports",
        help_text="The Pos this PosReport belongs to.",
    )

    bank_responsible = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="pos_reports_banker",
        help_text="The banker responsible for this PosReport",
    )

    pos_responsible = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="pos_reports_poser",
        help_text="The POS person responsible for this PosReport",
    )

    period = DateTimeRangeField(
        null=True,
        blank=True,
        help_text="The time period this report covers",
    )

    pos_json = models.JSONField(
        null=True,
        blank=True,
        help_text="The JSON exported from the external POS system",
    )

    comments = models.TextField(
        blank=True,
        help_text="Any comments about this PosReport",
    )

    dkk_sales_izettle = models.PositiveIntegerField(
        default=0,
        help_text="The total DKK amount in iZettle cash sales",
    )

    hax_sold_izettle = models.PositiveIntegerField(
        default=0,
        help_text="The number of HAX sold through the iZettle from the POS",
    )

    hax_sold_website_old = models.PositiveIntegerField(
        default=0,
        help_text="The number of HAX sold through webshop tickets being used in the POS. Not used anymore.",
    )

    # bank count start of day

    bank_count_dkk_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of DKK handed out from the bank to the POS at the start of the business day (counted by the bank responsible)",
    )

    bank_count_hax5_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of 5 HAX coins handed out from the bank to the POS at the start of the business day (counted by the bank responsible)",
    )

    bank_count_hax10_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of 10 HAX coins handed out from the bank to the POS at the start of the business day (counted by the bank responsible)",
    )

    bank_count_hax20_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of 20 HAX coins handed out from the bank to the POS at the start of the business day (counted by the bank responsible)",
    )

    bank_count_hax50_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of 50 HAX coins handed out from the bank to the POS at the start of the business day (counted by the bank responsible)",
    )

    bank_count_hax100_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of 100 HAX coins handed out from the bank to the POS at the start of the business day (counted by the bank responsible)",
    )

    # POS count start of day

    pos_count_dkk_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of DKK handed out from the bank to the POS at the start of the business day (counted by the POS responsible)",
    )

    pos_count_hax5_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of 5 HAX coins received by the POS from the bank at the start of the business day (counted by the POS responsible)",
    )

    pos_count_hax10_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of 10 HAX coins received by the POS from the bank at the start of the business day (counted by the POS responsible)",
    )

    pos_count_hax20_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of 20 HAX coins received by the POS from the bank at the start of the business day (counted by the POS responsible)",
    )

    pos_count_hax50_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of 50 HAX coins received by the POS from the bank at the start of the business day (counted by the POS responsible)",
    )

    pos_count_hax100_start = models.PositiveIntegerField(
        default=0,
        help_text="The number of 100 HAX coins received by the POS from the bank at the start of the business day (counted by the POS responsible)",
    )

    # bank count end of day

    bank_count_dkk_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of DKK handed back from the POS to the bank at the end of the business day (counted by the bank responsible)",
    )

    bank_count_hax5_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of 5 HAX coins handed back from the POS to the bank at the end of the business day (counted by the bank responsible)",
    )

    bank_count_hax10_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of 10 HAX coins handed back from the POS to the bank at the end of the business day (counted by the bank responsible)",
    )

    bank_count_hax20_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of 20 HAX coins handed back from the POS to the bank at the end of the business day (counted by the bank responsible)",
    )

    bank_count_hax50_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of 50 HAX coins handed back from the POS to the bank at the end of the business day (counted by the bank responsible)",
    )

    bank_count_hax100_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of 100 HAX coins handed back from the POS to the bank at the end of the business day (counted by the bank responsible)",
    )

    # pos count end of day

    pos_count_dkk_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of DKK handed back from the POS to the bank at the end of the business day (counted by the POS responsible)",
    )

    pos_count_hax5_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of 5 HAX coins received by the bank from the POS at the end of the business day (counted by the POS responsible)",
    )

    pos_count_hax10_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of 10 HAX coins received by the bank from the POS at the end of the business day (counted by the POS responsible)",
    )

    pos_count_hax20_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of 20 HAX coins received by the bank from the POS at the end of the business day (counted by the POS responsible)",
    )

    pos_count_hax50_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of 50 HAX coins received by the bank from the POS at the end of the business day (counted by the POS responsible)",
    )

    pos_count_hax100_end = models.PositiveIntegerField(
        default=0,
        help_text="The number of 100 HAX coins received by the bank from the POS at the end of the business day (counted by the POS responsible)",
    )

    @property
    def camp(self):
        return self.pos.team.camp

    camp_filter = "pos__team__camp"

    def get_absolute_url(self):
        return reverse(
            "backoffice:posreport_detail",
            kwargs={
                "camp_slug": self.camp.slug,
                "pos_slug": self.pos.slug,
                "posreport_uuid": self.uuid,
            },
        )

    @property
    def dkk_start_ok(self):
        return self.bank_count_dkk_start == self.pos_count_dkk_start

    @property
    def hax5_start_ok(self):
        return self.bank_count_hax5_start == self.pos_count_hax5_start

    @property
    def hax10_start_ok(self):
        return self.bank_count_hax10_start == self.pos_count_hax10_start

    @property
    def hax20_start_ok(self):
        return self.bank_count_hax20_start == self.pos_count_hax20_start

    @property
    def hax50_start_ok(self):
        return self.bank_count_hax50_start == self.pos_count_hax50_start

    @property
    def hax100_start_ok(self):
        return self.bank_count_hax100_start == self.pos_count_hax100_start

    @property
    def bank_start_hax(self):
        return (
            (self.bank_count_hax5_start * 5)
            + (self.bank_count_hax10_start * 10)
            + (self.bank_count_hax20_start * 20)
            + (self.bank_count_hax50_start * 50)
            + (self.bank_count_hax100_start * 100)
        )

    @property
    def pos_start_hax(self):
        return (
            (self.pos_count_hax5_start * 5)
            + (self.pos_count_hax10_start * 10)
            + (self.pos_count_hax20_start * 20)
            + (self.pos_count_hax50_start * 50)
            + (self.pos_count_hax100_start * 100)
        )

    @property
    def bank_end_hax(self):
        return (
            (self.bank_count_hax5_end * 5)
            + (self.bank_count_hax10_end * 10)
            + (self.bank_count_hax20_end * 20)
            + (self.bank_count_hax50_end * 50)
            + (self.bank_count_hax100_end * 100)
        )

    @property
    def pos_end_hax(self):
        return (
            (self.pos_count_hax5_end * 5)
            + (self.pos_count_hax10_end * 10)
            + (self.pos_count_hax20_end * 20)
            + (self.pos_count_hax50_end * 50)
            + (self.pos_count_hax100_end * 100)
        )

    @property
    def dkk_end_ok(self):
        return self.bank_count_dkk_end == self.pos_count_dkk_end

    @property
    def hax5_end_ok(self):
        return self.bank_count_hax5_end == self.pos_count_hax5_end

    @property
    def hax10_end_ok(self):
        return self.bank_count_hax10_end == self.pos_count_hax10_end

    @property
    def hax20_end_ok(self):
        return self.bank_count_hax20_end == self.pos_count_hax20_end

    @property
    def hax50_end_ok(self):
        return self.bank_count_hax50_end == self.pos_count_hax50_end

    @property
    def hax100_end_ok(self):
        return self.bank_count_hax100_end == self.pos_count_hax100_end

    def allok(self):
        return all(
            [
                self.dkk_start_ok,
                self.hax5_start_ok,
                self.hax10_start_ok,
                self.hax20_start_ok,
                self.hax50_start_ok,
                self.hax100_start_ok,
                self.dkk_end_ok,
                self.hax5_end_ok,
                self.hax10_end_ok,
                self.hax20_end_ok,
                self.hax50_end_ok,
                self.hax100_end_ok,
            ],
        )

    @property
    def pos_json_sales(self):
        """Calculate the total HAX sales and number of transactions."""
        transactions = 0
        total = 0
        if self.pos_json:
            for tx in self.pos_json:
                transactions += 1
                total += tx["amount"]
        return transactions, total

    @property
    def hax_balance(self):
        """Return the hax balance all things considered."""
        balance = 0
        # start by adding what the POS got at the start of the day
        balance += self.bank_start_hax
        # then substract the HAX the POS sold via the izettle
        balance -= self.hax_sold_izettle
        # then substract the HAX sold through webshop tickets
        balance -= self.hax_sold_website
        # then add the HAX sales from the POS json
        balance += self.pos_json_sales[1]
        # finally substract the HAX received from the POS at the end of the day
        balance -= self.bank_end_hax
        # all good
        return balance

    @property
    def dkk_balance(self):
        """Return the DKK balance all things considered."""
        balance = 0
        # start with the bank count at the start of the day
        balance += self.bank_count_dkk_start
        # then add the iZettle sales for the day
        balance += self.dkk_sales_izettle
        # then substract what was returned to the bank at days end
        balance -= self.bank_count_dkk_end
        # all good
        return balance

    @property
    def hax_sold_website(self):
        """Return the number of HAX handed out from checked in website shop tickets."""
        total = 0
        for st in ShopTicket.objects.filter(
            # we only care about tickets for the current camp
            ticket_type__camp=self.camp,
            # and only the 100 HAX product
            product__in=Product.objects.filter(name="100 HAX"),
            # and only for the current PoS
            used_pos=self.pos,
            # and only in the PoS period
            used_at__contained_by=self.period,
        ):
            total += st.quantity * 100
        return total


class PosProduct(ExportModelOperationsMixin("pos_product"), UUIDModel):
    """A product sold in our PoS. This model does not inherit from CampRelatedModel, meaning pos products are not camp specific."""

    external_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="The external ID of the product.",
    )

    brand_name = models.CharField(max_length=255, help_text="The name of the brand.")

    name = models.CharField(max_length=255, help_text="The name of the product.")

    description = models.TextField(
        blank=True,
        help_text="The description of the product.",
    )

    sales_price = models.IntegerField(help_text="The current price of this product.")

    unit_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The size of this product.",
    )

    size_unit = models.CharField(
        max_length=100,
        blank=True,
        help_text="The unit the size of this product is measured in, where applicable.",
    )

    abv = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        help_text="The ABV level of this product, where applicable.",
    )

    tags = models.CharField(
        max_length=100,
        blank=True,
        help_text="The tags for this product as a comma seperated string.",
    )

    expenses = models.ManyToManyField(
        "economy.Expense",
        blank=True,
        help_text="The related expenses for this PosProduct. Only expenses related to a Pos-team are shown. For products composed of multiple ingredients all relevant expenses should be picked.",
    )

    def __str__(self):
        return f"{self.brand_name} - {self.name} ({round(self.unit_size)}{self.size_unit})"


class PosTransaction(
    ExportModelOperationsMixin("pos_transaction"),
    CampRelatedModel,
    UUIDModel,
):
    """A transaction from the Pos system."""

    pos = models.ForeignKey(
        "economy.Pos",
        on_delete=models.PROTECT,
        related_name="pos_transactions",
        help_text="The Pos this PosTransaction belongs to.",
    )

    external_transaction_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="The external ID of this pos transaction.",
    )

    external_user_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="The external ID of the pos user who did this transaction.",
    )

    timestamp = models.DateTimeField(
        help_text="The date and time of this PoS transaction.",
    )

    @property
    def camp(self):
        return self.pos.team.camp

    camp_filter = "pos__team__camp"

    def __str__(self):
        return f"{self.pos} sale {self.timestamp}"


class PosSale(ExportModelOperationsMixin("pos_sale"), CampRelatedModel, UUIDModel):
    """A single product sold in a PoS transaction.

    Multiples of the same product result sold in a single tx results in multilpe PosSale objects.
    """

    transaction = models.ForeignKey(
        "economy.PosTransaction",
        on_delete=models.PROTECT,
        related_name="pos_sales",
        help_text="The transaction to which this sale belongs.",
    )

    product = models.ForeignKey(
        "economy.PosProduct",
        on_delete=models.PROTECT,
        related_name="pos_sales",
        help_text="The product being sold.",
    )

    sales_price = models.IntegerField(
        help_text="The price of this product (at the time of sale).",
    )

    @property
    def camp(self):
        return self.transaction.pos.team.camp

    camp_filter = "transaction__pos__team__camp"


class PosProductCost(
    ExportModelOperationsMixin("pos_product_cost"),
    CampRelatedModel,
    UUIDModel,
):
    """Defines the cost of PosProducts."""

    camp = models.ForeignKey(
        "camps.Camp",
        related_name="pos_product_costs",
        on_delete=models.PROTECT,
    )

    product = models.ForeignKey(
        "economy.PosProduct",
        on_delete=models.PROTECT,
        related_name="pos_product_costs",
        help_text="The product this cost applies to.",
    )

    timestamp = models.DateTimeField(
        help_text="The timestamp from which this product_cost is correct.",
    )

    product_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="The cost/expense (in DKK, including VAT) for each product sold. For products composed of multiple ingredients this number should include the total cost per product sold.",
    )


##################################
# bank stuff


class Bank(ExportModelOperationsMixin("bank"), CreatedUpdatedUUIDModel):
    """A bank where we have an account."""

    name = models.CharField(max_length=100, help_text="The name of the bank")

    def __str__(self):
        return self.name


class BankAccount(ExportModelOperationsMixin("bank_account"), CreatedUpdatedUUIDModel):
    """An account in our bank."""

    bank = models.ForeignKey(
        "economy.Bank",
        on_delete=models.PROTECT,
        related_name="accounts",
        help_text="The bank this bank account belongs to.",
    )

    name = models.CharField(max_length=100, help_text="The name of the bank account")

    reg_no = models.CharField(
        max_length=4,
        validators=[
            RegexValidator(
                regex="^[0-9]{4}$",
                message="Reg number must be 4 digits.",
                code="invalid_reg_no",
            ),
        ],
        help_text="The Danish reg. number of the bank account",
    )

    account_no = models.CharField(
        max_length=12,
        validators=[
            RegexValidator(
                regex="^[0-9]{6,12}$",
                message="Account number must be 6-12 digits.",
                code="invalid_account_no",
            ),
        ],
        help_text="The Danish account number of the bank account",
    )

    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="The date we began using this bank account.",
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="The date we stopped using this bank account.",
    )

    def __str__(self):
        return f"Account {self.name} (reg. {self.reg_no} account {self.account_no}) in bank {self.bank.name}"

    def import_csv(self, csvreader):
        """Import a CSV file with transactions for this bank account.

        assumes a CSV structure like this:

        "24-08-2021";"24-08-2021";"938d27e9-e559-4146-9d2e-be2dea";"-279,80";"230.119,11"
        "24-08-2021";"24-08-2021";"f1a7b16b-27d3-432f-bca7-2e2229";"-59,85";"230.398,91"
        "24-08-2021";"24-08-2021";"63e93a24-073b-4ebb-8b0d-5a3072";"-1.221,05";"230.458,76"

        The second date column is unused. Dates are in Europe/Copenhagen tz.
        """
        cph = pytz.timezone("Europe/Copenhagen")
        create_count = 0
        # Bank csv has the most recent lines first in the file, and the oldest last.
        # Read lines in reverse so we add the earliest transaction first,
        # this is important because bank csv transactions are only date stamped,
        # not time stamped. So we use the creation time of the db record in addition
        # to the transaction date for sorting.
        for row in reversed(list(csvreader)):
            # use update_or_create() so we can import a new CSV with the same transactions
            # but with updated descriptions, in case we fix a description in the bank
            tx, created = self.transactions.update_or_create(
                date=cph.localize(datetime.strptime(row[0], "%d-%m-%Y")),
                amount=Decimal(row[3].replace(".", "").replace(",", ".")),
                balance=Decimal(row[4].replace(".", "").replace(",", ".")),
                defaults={
                    "text": row[2],
                },
            )
            if created:
                create_count += 1
        return create_count

    def export_csv(self, period, workdir, filename=None):
        """Write a CSV file to disk with all transactions for the requested period."""
        if not filename:
            filename = f"bornhack_bank_account_{slugify(self.bank.name)}_{slugify(self.name)}_{self.reg_no}_{self.account_no}_{period.lower}_{period.upper}.csv"
        with open(workdir / filename, "w", newline="") as f:
            transactions = self.transactions.filter(
                date__gt=period.lower,
                date__lt=period.upper,
            )
            writer = csv.writer(f, dialect="excel")
            writer.writerow(["bornhack_uuid", "date", "text", "amount", "balance"])
            for tx in transactions:
                writer.writerow([tx.pk, tx.date, tx.text, tx.amount, tx.balance])
        return (self, filename, transactions.count())


class BankTransaction(
    ExportModelOperationsMixin("bank_transaction"),
    CreatedUpdatedUUIDModel,
):
    """A BankTransaction represents one movement into or out of the bank account."""

    class Meta:
        # include both date and created in the ordering,
        # (the bank CSV only includes date and not timestamp)
        get_latest_by = ["date", "created"]
        ordering = ["-date", "-created"]

    bank_account = models.ForeignKey(
        "economy.BankAccount",
        on_delete=models.PROTECT,
        related_name="transactions",
        help_text="The bank account this transaction belongs to.",
    )

    date = models.DateField(help_text="The date of this transaction.")

    text = models.CharField(max_length=255, help_text="The text for this transaction.")

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The amount of this transaction. Negative numbers means money left the bank account, positive numbers mean money was put into the bank account.",
    )

    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="The balance of the account after this transaction.",
    )

    def __str__(self):
        return f"Transaction {self.pk} for {self.amount} DKK with the text {self.text} on {self.date} on account {self.bank_account}"

    def clean(self):
        """Make sure transactions don't fall outside the bank accounts start and end dates."""
        if self.bank_account.start_date and self.date < self.bank_account.start_date:
            raise ValidationError(
                f"Transaction on {self.date} is before the bank accounts start_date. Transaction text is '{self.text}' and amount is {self.amount}",
            )
        if self.bank_account.end_date and self.date > self.bank_account.end_date:
            raise ValidationError(
                f"Transaction on {self.date} is after the bank accounts end_date. Transaction text is '{self.text}' and amount is {self.amount}",
            )


##################################
# Coinify stuff


class CoinifyInvoice(
    ExportModelOperationsMixin("coinify_invoice"),
    CreatedUpdatedUUIDModel,
):
    """Coinify creates one invoice every time a payment is completed."""

    class Meta:
        get_latest_by = ["coinify_created"]
        ordering = ["-coinify_created"]

    coinify_id = models.IntegerField(help_text="Coinifys internal ID for this invoice")
    coinify_id_alpha = models.CharField(
        max_length=20,
        help_text="Coinifys other internal ID for this invoice",
    )
    coinify_created = models.DateTimeField(help_text="Created datetime in Coinifys end")
    payment_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The payment amount",
    )
    payment_currency = models.CharField(max_length=3, help_text="The payment currency.")
    payment_btc_amount = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        help_text="The payment amount in BTC.",
    )
    description = models.TextField(
        help_text="The text description of this Coinify invoice",
    )
    custom = models.JSONField(
        null=True,
        blank=True,
        help_text="Custom JSON data for this invoice",
    )
    credited_amount = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        help_text="The amount credited on our Coinify account.",
    )
    credited_currency = models.CharField(
        max_length=3,
        help_text="The currency of the credited amount.",
    )
    state = models.CharField(
        max_length=100,
        help_text="The state of this Coinify invoice",
    )
    payment_type = models.CharField(
        max_length=100,
        help_text="The type of payment for this Coinify infoice. Extra means too much was paid on the original payment ID and a new invoice was created instead.",
    )
    original_payment_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="The original payment id (used when the invoice payment type is extra)",
    )


class CoinifyPaymentIntent(
    ExportModelOperationsMixin("coinify_payment_intent"),
    CreatedUpdatedUUIDModel,
):
    """Coinify Payment intents a intent is created for each payment."""

    class Meta:
        get_latest_by = ["coinify_created"]
        ordering = ["-coinify_created"]

    coinify_id = models.UUIDField(help_text="Coinifys internal ID for this invoice")
    coinify_created = models.DateTimeField(help_text="Created datetime in Coinifys end")
    reference_type = models.CharField(
        max_length=100,
        help_text="Coinifys reference type",
    )
    merchant_id = models.UUIDField(help_text="The Merchant ID in Coinify's system.")
    merchant_name = models.TextField(
        help_text="The Merchant name as set in Coinify's system.",
    )
    subaccount_id = models.CharField(
        max_length=32,
        help_text="Unique identifier of a created sub-account.",
        blank=True,
        null=True,
    )
    subaccount_name = models.TextField(
        help_text="Name given when creating the sub-account.",
        blank=True,
        null=True,
    )
    state = models.CharField(
        max_length=100,
        help_text="Coinify intent state",
    )
    state_reason = models.CharField(
        max_length=100,
        help_text="Coinify intent state reason",
    )
    original_order_id = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        help_text="Order id",
    )
    order = models.ForeignKey(
        "shop.Order",
        on_delete=models.PROTECT,
        related_name="economy_coinify_payment_intents",
        help_text="The Order this payment intent is for",
        blank=True,
        null=True,
    )
    api_payment_intent = models.ForeignKey(
        "shop.CoinifyAPIPaymentIntent",
        on_delete=models.PROTECT,
        related_name="economy_coinify_payment_intents",
        help_text="The original api payment intent",
        blank=True,
        null=True,
    )
    customer_email = models.TextField()
    requested_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The requested amount",
    )
    requested_currency = models.CharField(
        max_length=3,
        help_text="The requested currency.",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The payment amount",
        null=True,
    )
    currency = models.CharField(
        max_length=3,
        help_text="The payment currency.",
        null=True,
        blank=True,
    )


class CoinifySettlement(
    ExportModelOperationsMixin("coinify_settlement"),
    CreatedUpdatedUUIDModel,
):
    settlement_id = models.CharField(
        max_length=36,
        help_text="The internal coinify id for the settlement",
    )
    account = models.CharField(
        max_length=100,
        help_text="The settlement account",
    )
    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The gross amount",
    )
    fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The payout fee",
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The net amount",
    )
    payout_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The payout amount",
    )
    create_time = models.DateTimeField(
        help_text="Created datetime in Coinifys end for this payout",
    )


class CoinifyPayout(
    ExportModelOperationsMixin("coinify_payout"),
    CreatedUpdatedUUIDModel,
):
    """Coinify makes a payout every time our balance exceeds some preset amount in their end."""

    class Meta:
        get_latest_by = ["coinify_created"]
        ordering = ["-coinify_created"]

    coinify_id = models.IntegerField(help_text="Coinifys internal ID for this payout")
    coinify_created = models.DateTimeField(
        help_text="Created datetime in Coinifys end for this payout",
    )
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        help_text="The payout amount before fees",
    )
    fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The payout fee",
    )
    transferred = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The transferred amount after fees",
    )
    currency = models.CharField(max_length=3, help_text="The payout currency.")
    btc_txid = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="The BTC txid (used if this was a BTC payout).",
    )

    def to_dkk(self, amount, currency):
        """Quick currency conversion to DKK to help sorting."""
        if currency == "DKK":
            return amount
        if currency == "EUR":
            return amount * Decimal(7.5)
        # we should handle BTC payouts here if we ever start using them /tyk
        return amount

    @property
    def amount_dkk(self):
        """Convert to DKK to make it possible to sort tables with both EUR and DKK amounts."""
        return self.to_dkk(self.amount, self.currency)

    @property
    def fee_dkk(self):
        """Convert to DKK to make it possible to sort tables with both EUR and DKK amounts."""
        return self.to_dkk(self.fee, self.currency)

    @property
    def transferred_dkk(self):
        """Convert to DKK to make it possible to sort tables with both EUR and DKK amounts."""
        return self.to_dkk(self.transferred, self.currency)


class CoinifyBalance(
    ExportModelOperationsMixin("coinify_balance"),
    CreatedUpdatedUUIDModel,
):
    """Coinify balance objects show our balance in Coinifys end at UTC midnight daily."""

    class Meta:
        get_latest_by = ["date"]
        ordering = ["-date"]

    date = models.DateField(
        unique=True,
        help_text="The balance was recorded at UTC midnight at this date.",
    )
    btc = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        help_text="The BTC balance",
    )
    dkk = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The DKK balance",
    )
    eur = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The EUR balance",
    )


##################################
# ePay / Bambora and Clearhaus stuff


class EpayTransaction(
    ExportModelOperationsMixin("epay_transaction"),
    CreatedUpdatedUUIDModel,
):
    """ePay creates a transaction every time a card payment is completed through them."""

    class Meta:
        get_latest_by = ["auth_date"]
        ordering = ["-auth_date"]

    merchant_id = models.IntegerField(
        help_text="ePay merchant number for this transaction.",
    )
    transaction_id = models.IntegerField(help_text="ePays internal transaction ID.")
    order_id = models.IntegerField(
        help_text="The BornHack order ID for this ePay transaction.",
    )
    currency = models.CharField(max_length=3, help_text="The currency of this payment.")
    auth_date = models.DateTimeField(
        help_text="The date this payment was authorised by the user.",
    )
    auth_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The amount that was authorised by the user.",
    )
    captured_date = models.DateTimeField(
        help_text="The date this payment was captured.",
    )
    captured_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The amount that was captured.",
    )
    card_type = models.TextField(help_text="The card type used for this payment.")
    description = models.TextField(help_text="The description of this payment.")
    transaction_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The transaction fee for this payment.",
    )


class ClearhausSettlement(
    ExportModelOperationsMixin("clearhaus_settlement"),
    CreatedUpdatedUUIDModel,
):
    """Clearhaus creates a settlement (meaning they transfer money to us) weekly (if our balance is > 0)."""

    class Meta:
        get_latest_by = ["period_start_date"]
        ordering = ["-period_start_date"]

    merchant_id = models.IntegerField(help_text="The merchant ID in Clearhaus systems")
    merchant_name = models.CharField(
        max_length=255,
        help_text="The merchant name in Clearhaus systems",
    )
    clearhaus_uuid = models.UUIDField(
        help_text="The Clearhaus UUID for this settlement.",
    )
    settled = models.BooleanField(
        help_text="True if the settlement has been paid out, False if not.",
    )
    currency = models.CharField(
        max_length=3,
        help_text="The currency of this settlement.",
    )
    period_start_date = models.DateField(
        help_text="The first date of the period this settlement covers.",
    )
    period_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="The final date of the period this settlement covers. Can be empty if the period is still ongoing.",
    )
    payout_amount = models.DecimalField(
        null=True,
        blank=True,
        max_digits=12,
        decimal_places=2,
        help_text="The amount that was paid out in this settlement. Can be empty if the settlement has not been paid out yet.",
    )
    payout_date = models.DateField(
        null=True,
        blank=True,
        help_text="The date this settlement was paid out.",
    )
    summary_sales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The summary sales for this period",
    )
    summary_credits = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The summary credits for this period",
    )
    summary_refunds = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The summary refunds for this period",
    )
    summary_chargebacks = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The summary chargebacks for this period",
    )
    summary_fees = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The summary fees for this period",
    )
    summary_other_postings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The summary other postings for this period",
    )
    summary_net = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The summary net (total) for this period",
    )
    reserve_amount = models.DecimalField(
        null=True,
        blank=True,
        max_digits=12,
        decimal_places=2,
        help_text="The amount that has been reserved for later payout. Can be empty if nothing has been reserved for this period.",
    )
    reserve_date = models.DateField(
        null=True,
        blank=True,
        help_text="The date the reserve for this period will be paid out.",
    )
    fees_sales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for sales for this period",
    )
    fees_refunds = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for refunds for this period",
    )
    fees_authorisations = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for authorisations for this period",
    )
    fees_credits = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for credits for this period",
    )
    fees_minimum_processing = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for minimum processing for this period",
    )
    fees_service = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for service for this period",
    )
    fees_wire_transfer = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for wire transfers for this period",
    )
    fees_chargebacks = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for chargebacks for this period",
    )
    fees_retrieval_requests = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for retrieval requests for this period",
    )
    payout_reference_number = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="The Clearhaus reference number for the payout of this settlement. Can be empty if the settlement has not been paid out yet.",
    )
    payout_descriptor = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        help_text="The Clearhaus descriptor for the payout of this settlement. Can be empty if the settlement has not been paid out yet.",
    )
    reserve_reference_number = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="The Clearhaus reference number for the payout of the reserve of this settlement. Can be empty if there is no reserve or it the reserve has not been paid out yet.",
    )
    reserve_descriptor = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        help_text="The Clearhaus descriptor for the payout of the reserve of this settlement. Can be empty if the settlement has no reserve, or the reserve has not been paid out yet.",
    )
    fees_interchange = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for interchange for this period",
    )
    fees_scheme = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The fees for scheme for this period",
    )


##################################
# Zettle


class ZettleBalance(
    ExportModelOperationsMixin("zettle_balance"),
    CreatedUpdatedUUIDModel,
):
    """Zettle (formerly iZettle) creates an account statement line every time there is a movement affecting our balance."""

    class Meta:
        get_latest_by = ["statement_time"]
        ordering = ["-statement_time"]

    statement_time = models.DateTimeField(
        help_text="The date and time this movement was added to the account statement.",
    )
    payment_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The date and time this payment was made. Can be empty if this transaction is not a customer payment.",
    )
    payment_reference = models.IntegerField(
        null=True,
        blank=True,
        help_text="The reference for this payment. Can be empty if this transaction is not a customer payment.",
    )
    description = models.CharField(
        max_length=100,
        help_text="The description of this transaction.",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The amount of this transaction",
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Our balance in Zettles systems after this transaction.",
    )


class ZettleReceipt(
    ExportModelOperationsMixin("zettle_receipt"),
    CreatedUpdatedUUIDModel,
):
    """Zettle creates a receipt every time there is a customer payment or refund using Zettle. Not all receipts affect our Zettle balance (e.g. MobilePay payments are paid out by MobilePay directly)."""

    class Meta:
        get_latest_by = ["zettle_created"]
        ordering = ["-zettle_created"]

    zettle_created = models.DateTimeField(
        help_text="The date and time this receipt was created in Zettles end",
    )
    receipt_number = models.IntegerField(help_text="The Zettle receipt number.")
    vat = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The part of the total amount which is VAT",
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The total amount the customer paid",
    )
    fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The payment fee BornHack has to pay to receive this payment",
    )
    net = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The part of the payment which goes to BornHack after fees have been substracted.",
    )
    payment_method = models.CharField(max_length=100, help_text="The payment method")
    card_issuer = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        help_text="The card issuer. Can be empty if this was not a card payment.",
    )
    staff = models.CharField(
        max_length=100,
        help_text="The Zettle account which was used to make this sale.",
    )
    description = models.CharField(
        max_length=255,
        help_text="The description of this transaction.",
    )
    sold_via = models.CharField(max_length=100, help_text="Always POS?")


##################################
# MobilePay


class MobilePayTransaction(
    ExportModelOperationsMixin("mobilepay_transaction"),
    CreatedUpdatedUUIDModel,
):
    """MobilePay transactions cover payments/refunds, payouts, service fees and everything else."""

    event = models.CharField(
        max_length=100,
        help_text="The type of MobilePay transaction",
    )
    currency = models.CharField(
        max_length=3,
        help_text="The currency of this transaction.",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="The amount of this transaction",
    )
    mobilepay_created = models.DateTimeField(
        help_text="The MobilePay date and time for this transaction.",
    )
    comment = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text="The description of this transaction. Rarely used when MobilePay is used through Zettle.",
    )
    transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="The transaction id. Can be empty if the type of transaction is a transfer (bank payout).",
    )
    transfer_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="The ID of the transfer (payout) this transaction was included in. Can be empty if this transaction has not yet been included in a transfer.",
    )
    payment_point = models.CharField(
        max_length=100,
        help_text="The payment point. For now we only have one (which we rename from year to year)",
    )
    myshop_number = models.IntegerField(
        help_text="The MobilePay MyShop number for this payment. For now we only have one.",
    )
    bank_account = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="The bank account this transaction was transferred to. Can be empty if this is a payment (sale) which has not yet been included in a transfer.",
    )


##################################
# AccountingExport


class AccountingExport(
    ExportModelOperationsMixin("accounting_export"),
    CreatedUpdatedUUIDModel,
):
    date_from = models.DateField(
        help_text="The start date for this accounting export (YYYY-MM-DD).",
    )
    date_to = models.DateField(
        help_text="The end date for this accounting export (YYYY-MM-DD).",
    )
    comment = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text="Any economy team comment for this export. Optional.",
    )
    archive = models.FileField(
        upload_to="accountingexports/",
        help_text="The zipfile containing the exported accounting info (html+CSV files)",
    )

    def __str__(self):
        return f"AccountingExport from {self.date_from} to {self.date_to}"
