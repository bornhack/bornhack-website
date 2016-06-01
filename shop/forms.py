from django import forms
from .models import Order


class AddToOrderForm(forms.Form):
    quantity = forms.IntegerField(initial=1)

