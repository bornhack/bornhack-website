from django import forms
from .models import Ticket, TicketType


class TicketForm(forms.ModelForm):

    class Meta:
        model = Ticket
        fields = [
            'ticket_type',
            'payment_method',
        ]
        widgets = {
            'payment_method': forms.RadioSelect()
        }

    ticket_type = forms.ModelChoiceField(
        queryset=TicketType.objects.available()
    )


