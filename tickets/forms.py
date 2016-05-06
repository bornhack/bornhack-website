from django import forms
from .models import Ticket, TicketType


class TicketForm(forms.ModelForm):

    class Meta:
        model = Ticket
        fields = [
            'ticket_type',
        ]

    ticket_type = forms.ModelChoiceField(
        queryset=TicketType.objects.available()
    )

