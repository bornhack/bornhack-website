from __future__ import annotations

import json

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory

from program.models import Event
from program.models import Speaker
from tickets.models import ShopTicket
from tickets.models import TicketGroup


class AddRecordingForm(forms.ModelForm):
    recording_url = forms.URLField(
        label="Recording URL",
        help_text="Add a URL to the recording.",
        required=False,
    )

    class Meta:
        model = Event
        fields = ["video_recording", "recording_url"]


class AutoScheduleValidateForm(forms.Form):
    schedule = forms.ChoiceField(
        choices=(
            (
                "current",
                "Validate Current Schedule (Load the AutoScheduler with the currently scheduled Events and validate)",
            ),
            (
                "similar",
                "Validate Similar Schedule (Create and validate a new schedule based on the current schedule)",
            ),
            ("new", "Validate New Schedule (Create and validate a new schedule)"),
        ),
        help_text="What to validate?",
    )

    event_type_constraint = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Add event type based constraints (so a talk is not scheduled in a workshop slot and vice versa)",
    )

    speakers_other_events_constraint = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Add constraints for each speakers other events (so a speaker isn't scheduled to be in two or more places at once)",
    )

    speaker_event_conflicts_constraint = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Add constraints for each speakers event conflicts (so a speaker isn't scheduled at the same time as something they want to participate in)",
    )

    speaker_availability_constraint = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Add constraints for each speakers availability (so a speaker isn't scheduled when they are not available)",
    )


class AutoScheduleApplyForm(forms.Form):
    schedule = forms.ChoiceField(
        choices=(
            (
                "similar",
                "Apply Similar Schedule (Create and apply a new schedule similar to the current schedule)",
            ),
            (
                "new",
                "Apply New Schedule (Create and apply a new schedule without considering the current schedule)",
            ),
        ),
        help_text="Which schedule to apply?",
    )


class EventScheduleForm(forms.Form):
    """The EventSlots are added in the view and help_text is not visible, just define the field"""

    slot = forms.ChoiceField()


class SpeakerForm(forms.ModelForm):
    class Meta:
        model = Speaker
        fields = [
            "name",
            "email",
            "biography",
            "needs_oneday_ticket",
            "event_conflicts",
        ]

    def __init__(self, camp, matrix=None, *args, **kwargs):
        """Initialise the form and add availability fields to form"""
        super().__init__(*args, **kwargs)

        matrix = matrix or {}

        # do we have a matrix to work with?
        if not matrix:
            return
        # add speaker availability fields
        for date in matrix.keys():
            # do we need a column for this day?
            if not matrix[date]:
                # nothing on this day, skip it
                continue
            # loop over the daychunks for this day
            for daychunk in matrix[date]:
                if not matrix[date][daychunk]:
                    # no checkbox needed for this daychunk
                    continue
                # add the field
                self.fields[matrix[date][daychunk]["fieldname"]] = forms.BooleanField(
                    required=False,
                )
                # add it to Meta.fields too
                self.Meta.fields.append(matrix[date][daychunk]["fieldname"])

        # only show events from this camp
        self.fields["event_conflicts"].queryset = Event.objects.filter(
            track__camp=camp,
            event_type__support_speaker_event_conflicts=True,
        )


class BankCSVForm(forms.Form):
    def __init__(self, bank, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for account in bank.accounts.all():
            self.fields[str(account.pk)] = forms.FileField(
                help_text=f"CSV file for account '{account.name}'. Leave empty if you don't need to import anything for this account.",
                required=False,
            )


class CoinifyCSVForm(forms.Form):
    payment_intents = forms.FileField(
        help_text="CSV file with Coinify Payment Intents. Leave empty if no payment intents need to be imported.",
        required=False,
    )
    settlements = forms.FileField(
        help_text="CSV file with Coinify Settlements. Leave empty if no settlements need to be imported.",
        required=False,
    )
    invoices = forms.FileField(
        help_text="CSV file with Coinify invoices. Leave empty if no invoices need to be imported.",
        required=False,
    )
    payouts = forms.FileField(
        help_text="CSV file with Coinify payouts. Leave empty if no payouts need to be imported.",
        required=False,
    )
    balances = forms.FileField(
        help_text="CSV file with Coinify balances. Leave empty if no balances need to be imported.",
        required=False,
    )


class EpayCSVForm(forms.Form):
    transactions = forms.FileField(
        help_text="CSV file with ePay / Bambora transactions.",
    )


class ClearhausSettlementForm(forms.Form):
    settlements = forms.FileField(
        help_text="CSV file with Clearhaus Settlements. Importing the same settlements again will update values without creating duplicates.",
    )


class ZettleUploadForm(forms.Form):
    receipts = forms.FileField(
        help_text="Excel file with Zettle receipts. Importing the same receipts multiple times will not create duplicates. Leave this empty if you don't need to upload any receipts.",
        required=False,
    )
    balances = forms.FileField(
        help_text="Excel file with Zettle account statements and balances. Importing the same balances multiple times will not create duplicates. Leave this empty if you don't need to upload any acount statement/balances.",
        required=False,
    )


class MobilePayCSVForm(forms.Form):
    transfers = forms.FileField(
        help_text="CSV file with transfers and their related transactions. Importing the same transactions multiple times will not create duplicates. Leave this empty if you don't need to upload any transfers CSV.",
        required=False,
    )
    sales = forms.FileField(
        help_text="CSV file with MobilePay sales and refunds. Importing the same sales CSV multiple times will not create duplicates. Leave this empty if you don't need to upload any sales CSV.",
        required=False,
    )


class ShopTicketRefundForm(forms.ModelForm):
    class Meta:
        model = ShopTicket
        fields = ["refund"]

    refund = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["refund"].label = self.instance.name or "Unnamed ticket"


ShopTicketRefundFormSet = modelformset_factory(
    ShopTicket,
    form=ShopTicketRefundForm,
    extra=0,
)


class TicketGroupRefundForm(forms.ModelForm):
    class Meta:
        model = TicketGroup
        fields = ["refund"]

    refund = forms.BooleanField(required=False)


TicketGroupRefundFormSet = modelformset_factory(
    TicketGroup,
    form=TicketGroupRefundForm,
    extra=0,
)


class InvoiceDownloadForm(forms.Form):
    orders = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": "5"}))
    invoices = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": "5"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        return {
            "invoices": cleaned_data.get("invoices", "").split(),
            "orders": cleaned_data.get("orders", "").split(),
        }


class PosSalesJSONForm(forms.Form):
    sales = forms.FileField(
        help_text="POS sales.json file. Previously imported sales will be skipped and will not create duplicates.",
    )


class MapLayerFeaturesImportForm(forms.Form):
    """Form to import features in a map layer. Only accepts geojson type FeatureCollection."""

    geojson_data = forms.CharField(
        widget=forms.Textarea(),
        help_text="The GeoJSON geometries to import.",
    )

    def clean(self):
        """Parse geojson and return as dict."""
        cleaned_data = super().clean()
        # validate json
        try:
            geojson = json.loads(cleaned_data["geojson_data"])
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON")
        # validate geojson
        if "type" not in geojson or geojson["type"] != "FeatureCollection":
            raise ValidationError("Invalid GeoJSON - only FeatureCollection supported!")
        # all good
        return geojson


class ManageTeamPermissionsForm(forms.Form):
    """The form used in backoffice to manage permissions for a team."""

    def __init__(self, matrix: dict[str, list[str]], *args, **kwargs):
        """Build a form of bool fields for the teams users permissions."""
        super().__init__(*args, **kwargs)
        for username in matrix:
            for perm in matrix[username]:
                if perm in ["lead", "member"] or User.objects.get(username=username).is_superuser:
                    disabled = True
                else:
                    disabled = False
                self.fields[f"{username}_{perm}"] = forms.BooleanField(
                    label=perm,
                    required=False,
                    disabled=disabled,
                )
