import os

from django.db import models
from django.conf import settings
from django.db import models

from utils.email import add_outgoing_email
from utils.models import CampRelatedModel, UUIDModel


class Expense(CampRelatedModel, UUIDModel):
    camp = models.ForeignKey(
        'camps.Camp',
        on_delete=models.PROTECT,
        related_name='expenses',
        help_text='The camp to which this expense belongs',
    )

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='expenses',
        help_text='The user to which this expense belongs',
    )

    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text='The amount of this expense in DKK. Must match the amount on the invoice uploaded below.',
    )

    description = models.CharField(
        max_length=200,
        help_text='A short description of this expense. Please keep it meningful as it helps the Economy team a lot when categorising expenses. 200 characters or fewer.',
    )

    paid_by_bornhack = models.BooleanField(
        default=True,
        help_text="Leave checked if this expense was paid by BornHack. Uncheck if you need a reimbursement for this expense.",
    )

    invoice = models.ImageField(
        help_text='The invoice for this expense. Please make sure the amount on the invoice matches the amount you entered above. All common image formats are accepted.',
        upload_to='expenses/',
    )

    responsible_team = models.ForeignKey(
        'teams.Team',
        on_delete=models.PROTECT,
        related_name='expenses',
        help_text='The team to which this Expense belongs. A team responsible will need to approve the expense. When in doubt pick the Economy team.'
    )

    approved = models.NullBooleanField(
        default=None,
        help_text='True if this expense has been approved by the responsible team. False if it has been rejected. Blank if noone has decided yet.'
    )

    reimbursement = models.ForeignKey(
        'economy.Reimbursement',
        on_delete=models.PROTECT,
        related_name='expenses',
        null=True,
        blank=True,
        help_text='The reimbursement for this expense, if any. This is a dual-purpose field. If expense.paid_by_bornhack is true then expense.reimbursement references the reimbursement which this expense is created to cover. If expense.paid_by_bornhack is false then expense.reimbursement references the reimbursement which reimbursed this expense.'
    )

    notes = models.TextField(
        blank=True,
        help_text='Economy Team notes for this expense. Only visible to the Economy team and the submitting user.'
    )

    @property
    def invoice_filename(self):
        return os.path.basename(self.invoice.file.name)

    @property
    def approval_status(self):
        if self.approved == None:
            return "Pending approval"
        elif self.approved == True:
            return "Approved"
        else:
            return "Rejected"

    def approve(self):
        """
        This method marks an expense as approved.
        Approving an expense triggers an email to the economy system, and another email to the user who submitted the expense in the first place.
        """
        self.approved = True
        self.save()

        # Add email for this expense which will be sent to the accounting software
        add_outgoing_email(
            "emails/accountingsystem_email.txt",
            formatdict=dict(expense=self),
            subject="Expense for %s" % self.camp.title,
            to_recipients=[settings.ACCOUNTINGSYSTEM_EMAIL],
            attachment=self.invoice.path,
            attachment_filename=self.invoice.file.name,
        )

        # Add email which will be sent to the user who entered the expense
        add_outgoing_email(
            "emails/expense_approved_email.txt",
            formatdict=dict(expense=self),
            subject="Your expense for %s has been approved." % self.camp.title,
            to_recipients=[self.user.emailaddress_set.get(primary=True).email],
        )

    def reject(self):
        """
        This method marks an expense as not approved.
        Not approving an expense triggers an email to the user who submitted the expense in the first place.
        """
        self.approved = False
        self.save()

        # Add email which will be sent to the user who entered the expense
        add_outgoing_email(
            "emails/expense_rejected_email.txt",
            formatdict=dict(expense=self),
            subject="Your expense for %s has been rejected." % self.camp.title,
            to_recipients=[self.user.emailaddress_set.get(primary=True).email],
        )


class Reimbursement(CampRelatedModel, UUIDModel):
    """
    A reimbursement covers one or more expenses. 
    """
    camp = models.ForeignKey(
        'camps.Camp',
        on_delete=models.PROTECT,
        related_name='reimbursements',
        help_text='The camp to which this reimbursement belongs',
    )

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='created_reimbursements',
        help_text='The user who created this reimbursement.'
    )

    reimbursement_user = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='reimbursements',
        help_text='The user this reimbursement belongs to.'
    )

    notes = models.TextField(
        blank=True,
        help_text='Economy Team notes for this reimbursement. Only visible to the Economy team and the related user.'
    )

    paid = models.BooleanField(
        default=False,
        help_text="Check when this reimbursement has been paid to the user",
    )

    @property
    def amount(self):
        """
        The total amount for a reimbursement is calculated by adding up the amounts for all the related expenses
        """
        amount = 0
        for expense in self.expenses.all():
            amount += expense.amount
        return amount

