import os

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from utils.models import CampRelatedModel, CreatedUpdatedModel, UUIDModel
from utils.slugs import unique_slugify

from .email import (
    send_accountingsystem_expense_email,
    send_accountingsystem_revenue_email,
    send_expense_approved_email,
    send_expense_rejected_email,
    send_revenue_approved_email,
    send_revenue_rejected_email,
)


class ChainManager(models.Manager):
    """
    ChainManager adds 'expenses_total' and 'revenues_total' to the Chain qs
    """

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(expenses_total=models.Sum("credebtors__expenses__amount"))
        qs = qs.annotate(revenues_total=models.Sum("credebtors__revenues__amount"))
        return qs


class Chain(CreatedUpdatedModel, UUIDModel):
    """
    A chain of Credebtors. Used to group when several Creditors/Debtors
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
                    "slug", flat=True
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
    """
    CredebtorManager adds 'expenses_total' and 'revenues_total' to the Credebtor qs
    """

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(expenses_total=models.Sum("expenses__amount"))
        qs = qs.annotate(revenues_total=models.Sum("revenues__amount"))
        return qs


class Credebtor(CreatedUpdatedModel, UUIDModel):
    """
    The Credebtor model represents the specific "instance" of a Chain,
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
        """
        Generate slug as needed
        """
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.filter(
                    chain=self.chain
                ).values_list("slug", flat=True),
            )
        super().save(**kwargs)


class Revenue(CampRelatedModel, UUIDModel):
    """
    The Revenue model represents any type of income for BornHack.

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
        help_text="The invoice date for this Revenue. This must match the invoice date on the documentation uploaded below. Format is YYYY-MM-DD."
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

    @property
    def invoice_filename(self):
        return os.path.basename(self.invoice.file.name)

    @property
    def approval_status(self):
        if self.approved is None:
            return "Pending approval"
        elif self.approved:
            return "Approved"
        else:
            return "Rejected"

    def approve(self, request):
        """
        This method marks a revenue as approved.
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
        """
        This method marks a revenue as not approved.
        Not approving a revenue triggers an email to the user who submitted the revenue in the first place.
        """
        # mark as not approved and save
        self.approved = False
        self.save()

        # send email to the user
        send_revenue_rejected_email(revenue=self)

        # message to the browser
        messages.success(request, "Revenue %s rejected" % self.pk)


class Expense(CampRelatedModel, UUIDModel):
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
        help_text="The invoice date for this Expense. This must match the invoice date on the documentation uploaded below. Format is YYYY-MM-DD."
    )

    responsible_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="expenses",
        help_text="The team to which this Expense belongs. A team responsible will need to approve the expense. When in doubt pick the Economy team.",
    )

    approved = models.BooleanField(
        null=True,
        default=None,
        help_text="True if this expense has been approved by the responsible team. False if it has been rejected. Blank if noone has decided yet.",
    )

    reimbursement = models.ForeignKey(
        "economy.Reimbursement",
        on_delete=models.PROTECT,
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
        elif self.approved:
            return "Approved"
        else:
            return "Rejected"

    def approve(self, request):
        """
        This method marks an expense as approved.
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
        """
        This method marks an expense as not approved.
        Not approving an expense triggers an email to the user who submitted the expense in the first place.
        """
        # mark as not approved and save
        self.approved = False
        self.save()

        # send email to the user
        send_expense_rejected_email(expense=self)

        # message to the browser
        messages.success(request, "Expense %s rejected" % self.pk)


class Reimbursement(CampRelatedModel, UUIDModel):
    """
    A reimbursement covers one or more expenses.
    """

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
        help_text="The economy team member who created this reimbursement.",
    )

    reimbursement_user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="reimbursements",
        help_text="The user this reimbursement belongs to.",
    )

    notes = models.TextField(
        blank=True,
        help_text="Economy Team notes for this reimbursement. Only visible to the Economy team and the related user.",
    )

    paid = models.BooleanField(
        default=False,
        help_text="Check when this reimbursement has been paid to the user",
    )

    @property
    def covered_expenses(self):
        """
        Returns a queryset of all expenses covered by this reimbursement. Does not include the expense that paid for the reimbursement.
        """
        return self.expenses.filter(paid_by_bornhack=False)

    @property
    def amount(self):
        """
        The total amount for a reimbursement is calculated by adding up the amounts for all the related expenses
        """
        amount = 0
        for expense in self.expenses.filter(paid_by_bornhack=False):
            amount += expense.amount
        return amount


class Pos(CampRelatedModel, UUIDModel):
    """A Pos is a point-of-sale like the bar or infodesk."""

    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=255, help_text="The point-of-sale name")

    slug = models.SlugField(
        max_length=255,
        blank=True,
        help_text="Url slug for this POS. Leave blank to generate based on POS name.",
    )

    team = models.ForeignKey(
        "teams.Team", on_delete=models.PROTECT, help_text="The Team managning this POS",
    )

    def save(self, **kwargs):
        """Generate slug if needed."""
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.filter(
                    team__camp=self.team.camp
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


class PosReport(CampRelatedModel, UUIDModel):
    """A PosReport contains the HAX/DKK counts and the csv report from the POS system."""

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

    date = models.DateField(
        help_text="The date this report covers (pick the starting date if opening hours cross midnight).",
    )

    pos_json = models.JSONField(
        null=True,
        blank=True,
        help_text="The JSON exported from the external POS system",
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
