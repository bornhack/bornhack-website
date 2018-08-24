from django.conf import settings
from django.db import models

from utils.email import add_outgoing_email
from utils.models import CampRelatedModel, UUIDModel


class Reimbursement(CampRelatedModel, UUIDModel):
    camp = models.ForeignKey('camps.Camp', on_delete=models.PROTECT)
    user = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    description = models.TextField()
    receipt = models.ImageField()
    approved = models.NullBooleanField(default=None)

    def approve(self):
        self.approved = True
        self.save()

        # Add email which will be sent to the accounting software
        add_outgoing_email(
            "reimbursement/accounting_email.txt",
            formatdict=dict(reimbursement=self),
            subject=f"Reimbursement for {self.camp.title}",
            to_recipients=[settings.REIMBURSEMENT_MAIL],
            attachment=self.receipt.path,
            attachment_filename=self.receipt.file.name,
        )

        # Add email which will be sent to the user which has requested the reimbursement
        add_outgoing_email(
            "reimbursement/approved_email.txt",
            formatdict=dict(reimbursement=self),
            subject=f"Your reimbursement for {self.camp.title} has been approved.",
            to_recipients=[self.user.emailaddress_set.get(primary=True).email],
        )

    def reject(self):
        self.approved = False
        self.save()

        # Add email which will be sent to the user which has requested the reimbursement
        add_outgoing_email(
            "reimbursement/rejected_email.txt",
            formatdict=dict(reimbursement=self),
            subject=f"Your reimbursement for {self.camp.title} has been rejected.",
            to_recipients=[self.user.emailaddress_set.get(primary=True).email],
        )
