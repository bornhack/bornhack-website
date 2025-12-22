from __future__ import annotations

import copy

import magic
from django import forms

from .models import Expense
from .models import Revenue


class CleanInvoiceMixin:
    """We want our ImageFields to accept PDF files as well as images."""

    def clean_invoice(self):
        # get the uploaded file from cleaned_data
        uploaded_file = self.cleaned_data["invoice"]
        # is this a valid image?
        try:
            # create an ImageField instance
            im = forms.ImageField()
            # now check if the file is a valid image
            im.to_python(uploaded_file)
        except forms.ValidationError:
            # file is not a valid image, so check if it's a pdf
            # do a deep copy so we dont mess with the file object we might be passing on
            testfile = copy.deepcopy(uploaded_file)
            # read the uploaded file into memory (the webserver limits uploads to a reasonable max size so this should be safe)
            mimetype = magic.from_buffer(testfile.open().read(), mime=True)
            if mimetype != "application/pdf":
                raise forms.ValidationError("Only images and PDF files allowed")

        # this is either a valid image, or has mimetype application/pdf, all good
        return uploaded_file


class ExpenseUpdateForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            "description",
            "amount",
            "payment_status",
            "invoice_date",
        ]

    def __init__(self, *args, **kwargs):
        """Remove some choices."""
        super().__init__(*args, **kwargs)
        # TODO: this is a subset of the choices in the model,
        # find a way to keep this more DRY
        self.fields["payment_status"].choices = [
            (
                "Paid by BornHack",
                (
                    ("PAID_WITH_TYKLINGS_MASTERCARD", "Expense was paid with Tyklings BornHack Mastercard"),
                    ("PAID_WITH_AHFS_MASTERCARD", "Expense was paid with ahfs BornHack Mastercard"),
                    ("PAID_WITH_VIDIRS_MASTERCARD", "Expense was paid with Vidirs BornHack Mastercard"),
                    ("PAID_IN_NETBANK", "Expense was paid with bank transfer from BornHacks netbank"),
                    ("PAID_WITH_BORNHACKS_CASH", "Expense was paid with BornHacks cash"),
                ),
            ),
            (
                "Paid by Participant",
                (("PAID_NEEDS_REIMBURSEMENT", "Expense was paid by me, I need a reimbursement"),),
            ),
            (
                "Unpaid",
                (("UNPAID_NEEDS_PAYMENT", "Expense is unpaid"),),
            ),
        ]


class ExpenseCreateForm(ExpenseUpdateForm, CleanInvoiceMixin):
    invoice = forms.FileField()

    class Meta:
        model = Expense
        fields = [
            "description",
            "amount",
            "payment_status",
            "invoice_date",
            "invoice",
        ]


######### REVENUE ###############################


class RevenueUpdateForm(forms.ModelForm):
    class Meta:
        model = Revenue
        fields = ["description", "amount", "payment_status", "invoice_date"]

    def __init__(self, *args, **kwargs):
        """Remove some choices."""
        super().__init__(*args, **kwargs)
        # TODO: this is a subset of the choices in the model,
        # find a way to keep this more DRY
        self.fields["payment_status"].choices = [
            (
                "Paid to BornHack",
                (
                    ("PAID_TO_TYKLINGS_MASTERCARD", "Revenue was credited to Tyklings BornHack Mastercard"),
                    ("PAID_TO_AHFS_MASTERCARD", "Revenue was credited to ahfs BornHack Mastercard"),
                    ("PAID_TO_VIDIRS_MASTERCARD", "Revenue was credited to Vidirs BornHack Mastercard"),
                    ("PAID_IN_NETBANK", "Revenue was transferred to a BornHack bank account"),
                    ("PAID_IN_CASH", "Revenue was paid to BornHack with cash"),
                ),
            ),
            (
                "Paid to Participant",
                (("PAID_NEEDS_REDISBURSEMENT", "Revenue has been paid out to me, a redisbursement is needed"),),
            ),
            (
                "Unpaid",
                (("UNPAID_NEEDS_PAYMENT", "Revenue is unpaid"),),
            ),
        ]


class RevenueCreateForm(RevenueUpdateForm, CleanInvoiceMixin):
    invoice = forms.FileField()

    class Meta:
        model = Revenue
        fields = ["description", "amount", "payment_status", "invoice_date", "invoice"]
